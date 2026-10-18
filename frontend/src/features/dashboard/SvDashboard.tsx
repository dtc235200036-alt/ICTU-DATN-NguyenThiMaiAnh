import { useState } from 'react'
import { Button, Card, Col, Empty, List, Progress, Row, Skeleton, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router'

import { isAppPath, useMarkRead, useNotifications } from '../notifications/api'
import { trangThaiDeCuong } from '../outlines/constants'
import { formatDate, formatDateTime } from '../../utils/format'
import { useSvDashboard } from './api'
import type { SvDashboardOut } from './api'

const { Text } = Typography

const SHORTCUTS: { title: string; desc: string; to: string }[] = [
  { title: 'Đề tài của tôi', desc: 'Xem & quản lý đề tài được giao', to: '/de-tai-cua-toi' },
  { title: 'Nộp đề cương', desc: 'Nộp đề cương cho GVHD', to: '/de-cuong' },
  { title: 'Báo cáo tiến độ', desc: 'Cập nhật tiến độ thực hiện đồ án', to: '/tien-do' },
  { title: 'Lịch sử nộp', desc: 'Xem lại lịch sử nộp', to: '/lich-su-nop' },
  { title: 'Lịch bảo vệ', desc: 'Xem lịch bảo vệ đồ án tốt nghiệp', to: '/bao-ve' },
  { title: 'Kho đồ án', desc: 'Tài liệu, mẫu đồ án các khóa', to: '/kho-do-an' },
]

interface SummaryItem {
  label: string
  done: boolean
  status: string
  color: string
  to: string
}

function summaryOf(data: SvDashboardOut): SummaryItem[] {
  const deCuong = data.de_cuong?.trang_thai ?? 'CHUA_NOP'
  const daNopDeCuong = deCuong !== 'CHUA_NOP'
  const tongMoc = data.tien_do.length
  const daNopMoc = data.tien_do.filter((m) => m.trang_thai === 'DUNG_HAN' || m.trang_thai === 'NOP_TRE').length
  const treMoc = data.tien_do.some((m) => m.trang_thai === 'TRE_MOC')
  const daBaoVe = data.bao_ve?.diem_trung_binh !== null && data.bao_ve?.diem_trung_binh !== undefined
  return [
    {
      label: 'Nộp đề cương',
      done: deCuong === 'DA_DUYET',
      status: daNopDeCuong ? trangThaiDeCuong(deCuong).label : 'Chưa nộp',
      color: daNopDeCuong ? trangThaiDeCuong(deCuong).color : 'default',
      to: '/de-cuong',
    },
    {
      label: 'Báo cáo tiến độ',
      done: tongMoc > 0 && daNopMoc === tongMoc,
      status: tongMoc === 0 ? 'Chưa có mốc' : `Đã nộp ${daNopMoc}/${tongMoc}`,
      color: treMoc ? 'red' : daNopMoc === tongMoc && tongMoc > 0 ? 'success' : 'default',
      to: '/tien-do',
    },
    {
      label: 'Báo cáo cuối kỳ',
      done: data.bao_cao_cuoi_da_nop,
      status: data.bao_cao_cuoi_da_nop ? 'Đã nộp' : 'Chưa nộp',
      color: data.bao_cao_cuoi_da_nop ? 'success' : 'default',
      to: '/de-cuong?tab=bao-cao-cuoi',
    },
    {
      label: 'Bảo vệ đồ án',
      done: daBaoVe,
      status: daBaoVe ? 'Đã bảo vệ' : data.bao_ve ? `Chưa đến (${formatDate(data.bao_ve.ngay_bao_ve)})` : 'Chưa xếp lịch',
      color: daBaoVe ? 'success' : 'default',
      to: '/bao-ve',
    },
  ]
}

function NotificationCard() {
  const navigate = useNavigate()
  const [all, setAll] = useState(false)
  const { data, isLoading } = useNotifications(all ? 20 : 5)
  const markRead = useMarkRead()
  const items = data?.items ?? []

  return (
    <Card
      title="Thông báo mới"
      extra={
        <Button type="link" style={{ padding: 0 }} onClick={() => setAll((v) => !v)}>
          {all ? 'Thu gọn' : 'Xem tất cả'}
        </Button>
      }
      style={{ height: '100%' }}
    >
      {isLoading ? (
        <Skeleton active />
      ) : items.length === 0 ? (
        <Empty description="Chưa có thông báo" />
      ) : (
        <List
          dataSource={items}
          renderItem={(n) => (
            <List.Item
              style={{ cursor: isAppPath(n.lien_ket) ? 'pointer' : 'default' }}
              onClick={() => {
                if (!n.da_doc) markRead.mutate(n.id)
                if (isAppPath(n.lien_ket)) navigate(n.lien_ket)
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, width: '100%' }}>
                <span style={{ fontWeight: n.da_doc ? 400 : 600 }}>{n.noi_dung}</span>
                <Text type="secondary" style={{ whiteSpace: 'nowrap' }}>
                  {formatDateTime(n.thoi_diem)}
                </Text>
              </div>
            </List.Item>
          )}
        />
      )}
    </Card>
  )
}

function SummaryCard({ data }: { data: SvDashboardOut }) {
  const navigate = useNavigate()
  const items = summaryOf(data)
  const percent = Math.round((items.filter((i) => i.done).length / items.length) * 100)
  return (
    <Card title="Tóm tắt tiến độ" style={{ height: '100%' }}>
      <Row gutter={16} align="middle">
        <Col xs={24} sm={9} style={{ textAlign: 'center', marginBottom: 16 }}>
          <Progress type="circle" percent={percent} />
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">Hoàn thành các mốc quan trọng</Text>
          </div>
        </Col>
        <Col xs={24} sm={15}>
          <List
            dataSource={items}
            renderItem={(item) => (
              <List.Item
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(item.to)}
                extra={<Tag color={item.color}>{item.status}</Tag>}
              >
                {item.label}
              </List.Item>
            )}
          />
        </Col>
      </Row>
    </Card>
  )
}

/** Trang chủ SV: lối tắt chức năng, thông báo mới và tóm tắt tiến độ. */
export default function SvDashboard() {
  const navigate = useNavigate()
  const { data, isLoading } = useSvDashboard()

  return (
    <div>
      {data?.de_tai ? (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Text strong>{data.de_tai.ten_de_tai}</Text>
          <Text type="secondary"> · GVHD: {data.de_tai.giang_vien_huong_dan ?? '—'}</Text>
        </Card>
      ) : (
        !isLoading && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Text type="secondary">
              Bạn chưa được giao đề tài
              {data?.giang_vien_huong_dan ? ` — GVHD: ${data.giang_vien_huong_dan}` : ''}. Khi GVHD giao
              đề tài trên hệ thống, bạn sẽ nhận được thông báo.
            </Text>
          </Card>
        )
      )}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {SHORTCUTS.map((s) => (
          <Col key={s.to} xs={12} md={8} xl={4}>
            <Card hoverable onClick={() => navigate(s.to)} style={{ height: '100%', textAlign: 'center' }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>{s.title}</div>
              <Text type="secondary">{s.desc}</Text>
            </Card>
          </Col>
        ))}
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <NotificationCard />
        </Col>
        <Col xs={24} lg={12}>
          {isLoading || !data ? (
            <Card title="Tóm tắt tiến độ">
              <Skeleton active />
            </Card>
          ) : (
            <SummaryCard data={data} />
          )}
        </Col>
      </Row>
    </div>
  )
}
