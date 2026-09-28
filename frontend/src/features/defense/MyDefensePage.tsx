import { Alert, Card, Col, Divider, Empty, Row, Skeleton, Statistic, Tag, Typography } from 'antd'
import { Link } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { formatDate } from '../../utils/format'
import { useMyDefense } from './api'
import type { VaiTroThanhVien } from './api'

const { Text } = Typography

const VAI_TRO_LABEL: Record<VaiTroThanhVien, string> = {
  CHU_TICH: 'Chủ tịch',
  THU_KY: 'Thư ký',
  UY_VIEN: 'Ủy viên',
}

/**
 * UC4.5/MH-02 ("Lịch và kết quả bảo vệ"): SV xem hội đồng, ngày giờ, phòng
 * và thành viên; điểm bảo vệ CHỈ xuất hiện sau khi Bộ môn chốt (D-06 — server
 * không trả ket_qua trước đó).
 */
export default function MyDefensePage() {
  const { data, isLoading, isError, error } = useMyDefense()

  if (isLoading) {
    return (
      <Card title="Lịch và kết quả bảo vệ">
        <Skeleton active />
      </Card>
    )
  }

  if (isError || !data) {
    return (
      <Card title="Lịch và kết quả bảo vệ">
        <Alert type="error" showIcon message={getErrorMessage(error)} />
      </Card>
    )
  }

  if (!data.lich) {
    return (
      <Card title="Lịch và kết quả bảo vệ">
        <Empty description="Bạn chưa được xếp lịch bảo vệ">
          <Link to="/de-cuong?tab=bao-cao-cuoi">Nộp báo cáo cuối</Link>
        </Empty>
      </Card>
    )
  }

  const lich = data.lich
  return (
    <Card title="Lịch và kết quả bảo vệ" style={{ maxWidth: 720 }}>
      <Row gutter={24}>
        <Col xs={24} md={15}>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{`${lich.ten_hoi_dong} · Phòng ${lich.phong}`}</div>
          <Text type="secondary">{`${formatDate(lich.ngay_bao_ve)} · ${lich.gio_du_kien}`}</Text>
          <Divider style={{ margin: '12px 0' }} />
          {lich.thanh_vien.map((m, idx) => (
            <div key={`${m.vai_tro}-${idx}`} style={{ marginBottom: 4 }}>
              {`${VAI_TRO_LABEL[m.vai_tro]}: ${[m.hoc_vi, m.ho_ten].filter(Boolean).join(' ')}`}
            </div>
          ))}
        </Col>
        <Col xs={24} md={9}>
          {data.ket_qua ? (
            <Statistic title="Điểm bảo vệ" value={data.ket_qua.diem_trung_binh} precision={2} />
          ) : (
            <div>
              <div style={{ color: 'rgba(0,0,0,0.45)', marginBottom: 8 }}>Điểm bảo vệ</div>
              <Tag>Chưa có kết quả</Tag>
            </div>
          )}
        </Col>
      </Row>
    </Card>
  )
}
