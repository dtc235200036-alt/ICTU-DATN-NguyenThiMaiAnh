import { Alert, Button, Card, Col, Empty, List, Row, Skeleton, Statistic, Steps, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router'

import CheckStatusTag from '../documents/CheckStatusTag'
import { isAppPath, useNotifications, useUnreadCount } from '../notifications/api'
import { TRANG_THAI_MOC, formatDay } from '../progress/constants'
import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { formatDate, formatPercent, formatRelative } from '../../utils/format'
import { useSvDashboard } from './api'
import type { SvDashboardOut } from './api'

const { Text } = Typography

// OUTL-02/MH-02: nhãn trạng thái đề cương (cùng bảng màu với OutlinePage).
const TRANG_THAI_DE_CUONG: Record<string, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

function TopicCard({ data }: { data: SvDashboardOut }) {
  const navigate = useNavigate()
  const { de_tai, co_dot_dang_mo, giang_vien_huong_dan } = data
  const trangThai = de_tai
    ? (TRANG_THAI_DE_TAI[de_tai.trang_thai] ?? { label: de_tai.trang_thai, color: 'default' })
    : null

  return (
    <Card title="Đề tài của tôi" style={{ height: '100%' }}>
      {de_tai ? (
        <>
          <p style={{ margin: '0 0 8px', fontWeight: 500 }}>{de_tai.ten_de_tai}</p>
          <p style={{ margin: '0 0 4px', color: 'rgba(0,0,0,0.45)' }}>
            GVHD: {de_tai.giang_vien_huong_dan ?? '—'}
          </p>
          <p style={{ margin: '0 0 12px' }}>
            <Tag color={trangThai?.color}>{trangThai?.label}</Tag>
          </p>
          {de_tai.trang_thai === 'TU_CHOI' && (
            <Alert
              type="error"
              showIcon
              message={`Lý do từ chối: ${de_tai.ly_do_tu_choi ?? ''}`}
              style={{ marginBottom: 12 }}
            />
          )}
          <Button onClick={() => navigate(`/de-tai/${de_tai.id}`)}>Xem chi tiết đề tài</Button>
        </>
      ) : (
        <Empty
          description={
            giang_vien_huong_dan
              ? `Bạn chưa có đề tài — GVHD của bạn: ${giang_vien_huong_dan}`
              : co_dot_dang_mo
                ? 'Bạn chưa có đề tài và chưa được Bộ môn phân công GVHD'
                : 'Bạn chưa có đề tài'
          }
        >
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <Button
              type="primary"
              disabled={!co_dot_dang_mo || !giang_vien_huong_dan}
              title={co_dot_dang_mo ? undefined : 'Chưa có đợt đồ án đang mở'}
              onClick={() => navigate('/de-tai/de-xuat')}
            >
              Đề xuất đề tài
            </Button>
            <Button
              disabled={!co_dot_dang_mo || !giang_vien_huong_dan}
              title={co_dot_dang_mo ? undefined : 'Chưa có đợt đồ án đang mở'}
              onClick={() => navigate('/de-tai')}
            >
              Đăng ký đề tài GVHD mở
            </Button>
          </div>
        </Empty>
      )}
    </Card>
  )
}

function NotificationCard() {
  const navigate = useNavigate()
  const unread = useUnreadCount()
  const { data, isLoading } = useNotifications(3)
  const items = data?.items ?? []

  return (
    <Card title={`Thông báo (${unread.data?.chua_doc ?? data?.chua_doc ?? 0} chưa đọc)`} style={{ height: '100%' }}>
      <List
        loading={isLoading}
        locale={{ emptyText: 'Chưa có thông báo' }}
        dataSource={items}
        renderItem={(item) => (
          <List.Item
            style={{ cursor: isAppPath(item.lien_ket) ? 'pointer' : undefined }}
            onClick={() => {
              if (isAppPath(item.lien_ket)) navigate(item.lien_ket)
            }}
          >
            <div>
              <div style={{ fontWeight: item.da_doc ? 400 : 600 }}>{item.noi_dung}</div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatRelative(item.thoi_diem)}
              </Text>
            </div>
          </List.Item>
        )}
      />
    </Card>
  )
}

function OutlineCard({ data }: { data: SvDashboardOut }) {
  const navigate = useNavigate()
  const dc = data.de_cuong
  if (!dc) {
    return (
      <Card title="Đề cương" style={{ height: '100%' }}>
        <Text type="secondary">Đề cương mở khi đề tài đã được phân công GVHD.</Text>
      </Card>
    )
  }
  const meta = TRANG_THAI_DE_CUONG[dc.trang_thai] ?? { label: dc.trang_thai, color: 'default' }
  return (
    <Card
      title="Đề cương"
      style={{ height: '100%' }}
      extra={<a onClick={() => navigate('/de-cuong')}>Mở đề cương</a>}
    >
      <p style={{ margin: '0 0 8px' }}>
        {dc.phien_ban
          ? `Phiên bản mới nhất: v${dc.phien_ban} · nộp ${formatDate(dc.thoi_diem_nop)}`
          : 'Chưa nộp phiên bản nào'}
      </p>
      <p style={{ margin: '0 0 12px' }}>
        <Tag color={meta.color}>{meta.label}</Tag>
      </p>
      {dc.kiem_tra && dc.kiem_tra.trang_thai === 'HOAN_TAT' ? (
        <Statistic title="Tỷ lệ trùng lặp gần nhất" value={formatPercent(dc.kiem_tra.ty_le_tong)} />
      ) : (
        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
            Tỷ lệ trùng lặp gần nhất
          </Text>
          <CheckStatusTag kiemTra={dc.kiem_tra} />
        </div>
      )}
    </Card>
  )
}

function ProgressCard({ data }: { data: SvDashboardOut }) {
  const navigate = useNavigate()
  const { tien_do, moc_tiep_theo } = data
  const current = tien_do.findIndex((m) => m.trang_thai === 'CHUA_DEN_HAN')

  return (
    <Card
      title="Tiến độ"
      style={{ height: '100%' }}
      extra={tien_do.length > 0 ? <a onClick={() => navigate('/tien-do')}>Nộp báo cáo</a> : undefined}
    >
      {tien_do.length === 0 ? (
        <Text type="secondary">Chưa có mốc tiến độ cho đề tài của bạn.</Text>
      ) : (
        <>
          <Steps
            size="small"
            current={current === -1 ? tien_do.length : current}
            items={tien_do.map((m) => {
              const s = TRANG_THAI_MOC[m.trang_thai]
              const late = m.trang_thai === 'TRE_MOC' || m.trang_thai === 'NOP_TRE'
              return {
                title: m.ten_moc,
                status: late ? 'error' : m.trang_thai === 'DUNG_HAN' ? 'finish' : 'wait',
                description:
                  m.trang_thai === 'CHUA_DEN_HAN' ? `Hạn ${formatDay(m.han_nop)}` : s.label,
              }
            })}
          />
          {moc_tiep_theo && (
            <p style={{ margin: '16px 0 0' }}>
              {moc_tiep_theo.con_ngay !== null
                ? `Mốc tiếp theo: ${moc_tiep_theo.ten_moc} - còn ${moc_tiep_theo.con_ngay} ngày`
                : `Mốc tiếp theo: ${moc_tiep_theo.ten_moc}`}
            </p>
          )}
        </>
      )}
    </Card>
  )
}

function DefenseCard({ data }: { data: SvDashboardOut }) {
  const bv = data.bao_ve
  return (
    <Card title="Lịch và kết quả bảo vệ" style={{ height: '100%' }}>
      {bv ? (
        <>
          <p style={{ margin: '0 0 4px', fontWeight: 500 }}>{`${bv.ten_hoi_dong} · Phòng ${bv.phong}`}</p>
          <p style={{ margin: '0 0 4px' }}>{`${formatDay(bv.ngay_bao_ve)} · ${bv.gio_du_kien}`}</p>
          <p style={{ margin: '0 0 12px', color: 'rgba(0,0,0,0.45)' }}>
            {`Chủ tịch: ${bv.chu_tich ?? '—'}`}
          </p>
          {bv.diem_trung_binh !== null ? (
            <Statistic title="Điểm bảo vệ" value={bv.diem_trung_binh} precision={2} />
          ) : (
            <Tag>Chưa có kết quả</Tag>
          )}
        </>
      ) : (
        <Text type="secondary">Chưa được xếp lịch bảo vệ</Text>
      )}
    </Card>
  )
}

/** MH-02: đề tài + thông báo + đề cương + tiến độ + lịch/kết quả bảo vệ của SV. */
export default function SvDashboard() {
  const { data, isLoading } = useSvDashboard()

  if (isLoading || !data) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={14}>
        <TopicCard data={data} />
      </Col>
      <Col xs={24} lg={10}>
        <NotificationCard />
      </Col>
      <Col xs={24} lg={8}>
        <OutlineCard data={data} />
      </Col>
      <Col xs={24} lg={16}>
        <ProgressCard data={data} />
      </Col>
      <Col xs={24} lg={12}>
        <DefenseCard data={data} />
      </Col>
    </Row>
  )
}
