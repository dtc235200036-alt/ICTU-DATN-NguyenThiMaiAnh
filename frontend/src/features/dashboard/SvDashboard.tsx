import { Alert, Button, Card, Empty, Skeleton, Tag } from 'antd'
import { useNavigate } from 'react-router'

import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { useSvDashboard } from './api'

/** MH-02 (subset Phase 2): đề tài đang hoạt động (hoặc gần nhất) của SV. */
export default function SvDashboard() {
  const navigate = useNavigate()
  const { data, isLoading } = useSvDashboard()

  if (isLoading || !data) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  const { de_tai, co_dot_dang_mo } = data
  const trangThai = de_tai ? (TRANG_THAI_DE_TAI[de_tai.trang_thai] ?? { label: de_tai.trang_thai, color: 'default' }) : null

  return (
    <Card title="Đề tài của tôi">
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
        <Empty description="Bạn chưa có đề tài">
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <Button
              type="primary"
              disabled={!co_dot_dang_mo}
              title={co_dot_dang_mo ? undefined : 'Chưa có đợt đồ án đang mở'}
              onClick={() => navigate('/de-tai/de-xuat')}
            >
              Đề xuất đề tài
            </Button>
            <Button
              disabled={!co_dot_dang_mo}
              title={co_dot_dang_mo ? undefined : 'Chưa có đợt đồ án đang mở'}
              onClick={() => navigate('/de-tai')}
            >
              Đăng ký đề tài có sẵn
            </Button>
          </div>
        </Empty>
      )}
    </Card>
  )
}
