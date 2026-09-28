import { useState } from 'react'
import { Badge, Button, Empty, Popover, Spin, Typography } from 'antd'
import { useNavigate } from 'react-router'

import QueryErrorAlert from '../../components/QueryErrorAlert'
import { formatRelative } from '../../utils/format'
import {
  isAppPath,
  useMarkAllRead,
  useMarkRead,
  useNotifications,
  useUnreadCount,
  type NotificationOut,
} from './api'

/** D-08/T-03-SC: icon chuông SVG nội tuyến — không thêm @ant-design/icons. */
function BellIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  )
}

function NotificationItem({
  item,
  onOpen,
}: {
  item: NotificationOut
  onOpen: (item: NotificationOut) => void
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(item)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onOpen(item)
      }}
      style={{
        display: 'flex',
        gap: 10,
        padding: '10px 16px',
        cursor: 'pointer',
        borderBottom: '1px solid #f0f0f0',
        background: item.da_doc ? '#fff' : '#f0f7ff',
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          marginTop: 7,
          flex: 'none',
          background: item.da_doc ? 'transparent' : '#1677ff',
        }}
      />
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: item.da_doc ? 400 : 600, wordBreak: 'break-word' }}>
          {item.noi_dung}
        </div>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {formatRelative(item.thoi_diem)}
        </Typography.Text>
      </div>
    </div>
  )
}

/**
 * UC0.5/NOTF-01/MH-02: chuông ở Header — badge số chưa đọc (polling 30 s),
 * mở ra 10 thông báo mới nhất; bấm một mục = đánh dấu đã đọc + điều hướng
 * tới lien_ket nội bộ; "Đánh dấu tất cả đã đọc" xóa badge.
 */
export default function NotificationBell() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const unread = useUnreadCount()
  const list = useNotifications(10, open)
  const markRead = useMarkRead()
  const markAll = useMarkAllRead()

  const chuaDoc = unread.data?.chua_doc ?? 0
  const items = list.data?.items ?? []

  const handleOpen = (item: NotificationOut) => {
    if (!item.da_doc) markRead.mutate(item.id)
    setOpen(false)
    if (isAppPath(item.lien_ket)) navigate(item.lien_ket)
  }

  const content = (
    <div style={{ width: 360 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <Typography.Text strong>{`Thông báo (${chuaDoc} chưa đọc)`}</Typography.Text>
        <Button
          type="link"
          size="small"
          style={{ padding: 0 }}
          disabled={chuaDoc === 0}
          loading={markAll.isPending}
          onClick={() => markAll.mutate()}
        >
          Đánh dấu tất cả đã đọc
        </Button>
      </div>
      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        {list.isLoading ? (
          <div style={{ padding: 24, textAlign: 'center' }}>
            <Spin />
          </div>
        ) : list.isError ? (
          <div style={{ padding: 12 }}>
            <QueryErrorAlert error={list.error} onRetry={() => void list.refetch()} />
          </div>
        ) : items.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Chưa có thông báo"
            style={{ padding: '16px 0' }}
          />
        ) : (
          items.map((item) => <NotificationItem key={item.id} item={item} onOpen={handleOpen} />)
        )}
      </div>
    </div>
  )

  return (
    <Popover
      trigger="click"
      placement="bottomRight"
      open={open}
      onOpenChange={setOpen}
      content={content}
      arrow={false}
      styles={{ body: { padding: 0 } }}
    >
      <Button type="text" aria-label="Thông báo" data-testid="notification-bell">
        <Badge count={chuaDoc} overflowCount={99} size="small" offset={[4, -2]}>
          <span style={{ color: 'rgba(0,0,0,0.65)', display: 'inline-flex' }}>
            <BellIcon />
          </span>
        </Badge>
      </Button>
    </Popover>
  )
}
