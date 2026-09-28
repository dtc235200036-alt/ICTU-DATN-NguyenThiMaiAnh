import type { ReactNode } from 'react'
import { App as AntApp, Alert, Button, Card, Skeleton, Spin, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { useNavigate } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { formatPercent } from '../../utils/format'
import { useDocumentCheck, useRecheck } from './api'
import type { CheckMatch } from './api'

export interface CheckPanelProps {
  taiLieuId: number | undefined
  canRecheck: boolean
  pendingText?: string
}

const DEFAULT_PENDING_TEXT =
  'Đang kiểm tra, chưa có kết quả. GVHD vẫn có thể xem nội dung và duyệt/yêu cầu sửa đề cương.'

// chi_tiet/do_an_trung được document_check ghi nhãn "{ten_de_tai} ({khoa})" —
// cột Khóa là phần "(...)" cuối cùng, rỗng khi nhãn không có khóa (Fact cố
// định lúc lập kế hoạch, 03-02-PLAN.md).
function parseMatchLabel(label: string): { ten: string; khoa: string } {
  const match = /^(.*)\s\(([^()]*)\)\s*$/.exec(label)
  if (match) {
    return { ten: match[1], khoa: match[2] }
  }
  return { ten: label, khoa: '' }
}

const matchColumns: ColumnsType<CheckMatch> = [
  {
    title: 'Tên đồ án',
    key: 'ten',
    render: (_value, record) => parseMatchLabel(record.doi_tuong_trung).ten,
  },
  {
    title: 'Khóa',
    key: 'khoa',
    render: (_value, record) => parseMatchLabel(record.doi_tuong_trung).khoa || '—',
  },
  { title: 'Tỷ lệ', key: 'ty_le', render: (_value, record) => formatPercent(record.ty_le) },
]

/**
 * MH-09/D-04: panel "Kết quả kiểm tra trùng lặp" dùng chung bởi đề cương
 * (03-02), báo cáo tiến độ, báo cáo cuối và chấm điểm (các plan sau). Không
 * bao giờ chặn duyệt/yêu cầu sửa khi đang DANG_KIEM_TRA (UC2.2 - E1).
 */
export default function CheckPanel({ taiLieuId, canRecheck, pendingText }: CheckPanelProps) {
  const { message } = AntApp.useApp()
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useDocumentCheck(taiLieuId)
  const recheckMutation = useRecheck()

  const handleRecheck = async () => {
    if (taiLieuId === undefined) return
    try {
      await recheckMutation.mutateAsync(taiLieuId)
      message.success('Đã yêu cầu kiểm tra lại')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  let body: ReactNode
  if (isLoading) {
    body = <Skeleton active paragraph={{ rows: 3 }} />
  } else if (isError) {
    const status = error instanceof AxiosError ? error.response?.status : undefined
    body =
      status === 404 ? (
        <p style={{ margin: 0, color: 'rgba(0,0,0,0.45)' }}>Chưa có kết quả kiểm tra</p>
      ) : (
        <Alert type="error" showIcon message="Không tải được kết quả kiểm tra" />
      )
  } else if (!data || data.trang_thai === 'DANG_KIEM_TRA') {
    body = (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          padding: '24px 0',
        }}
      >
        <Spin />
        <p style={{ margin: 0, fontSize: 13, color: 'rgba(0,0,0,0.45)', textAlign: 'center' }}>
          {pendingText ?? DEFAULT_PENDING_TEXT}
        </p>
      </div>
    )
  } else if (data.trang_thai === 'LOI') {
    body = (
      <Alert
        type="warning"
        showIcon
        message="Kiểm tra trùng lặp gặp lỗi — tài liệu vẫn được xử lý bình thường (UC0.7 - E1)"
        description={
          data.tai_lieu.trich_xuat_loi
            ? 'Không trích xuất được nội dung file — cần nộp lại file khác để kiểm tra.'
            : undefined
        }
        action={
          canRecheck && !data.tai_lieu.trich_xuat_loi ? (
            <Button size="small" loading={recheckMutation.isPending} onClick={handleRecheck}>
              Kiểm tra lại
            </Button>
          ) : undefined
        }
      />
    )
  } else {
    const overThreshold = (data.ty_le_tong ?? 0) > data.nguong_ap_dung
    body = (
      <div>
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <div style={{ fontSize: 32, fontWeight: 600, lineHeight: 1.2 }}>
            {formatPercent(data.ty_le_tong)}
          </div>
          <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>tỷ lệ tổng</div>
        </div>
        <p
          style={{
            textAlign: 'center',
            margin: '0 0 16px',
            fontSize: 12,
            color: 'rgba(0,0,0,0.45)',
          }}
        >
          Ngưỡng áp dụng của Bộ môn: <strong>{formatPercent(data.nguong_ap_dung)}</strong> (UC0.4)
          {' · '}
          <Tag color={overThreshold ? 'error' : 'success'}>
            {overThreshold ? 'Vượt ngưỡng cảnh báo' : 'Dưới ngưỡng cảnh báo'}
          </Tag>
        </p>
        <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 500 }}>Đồ án trùng nhiều nhất</p>
        <Table<CheckMatch>
          size="small"
          rowKey="doi_tuong_trung"
          pagination={false}
          columns={matchColumns}
          dataSource={data.do_an_trung.slice(0, 3)}
          locale={{ emptyText: 'Không phát hiện đồ án trùng' }}
        />
        <Button
          block
          style={{ marginTop: 16 }}
          onClick={() => navigate(`/kiem-tra-trung-lap/${taiLieuId}`)}
        >
          Xem chi tiết
        </Button>
      </div>
    )
  }

  return <Card title="Kết quả kiểm tra trùng lặp">{body}</Card>
}
