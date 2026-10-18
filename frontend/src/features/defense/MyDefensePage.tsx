import { Alert, Card, Empty, Skeleton, Statistic, Table, Tag, Typography } from 'antd'
import { Link } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { formatDate } from '../../utils/format'
import { useSvDashboard } from '../dashboard/api'
import { useMyDefense } from './api'
import type { VaiTroThanhVien } from './api'

const { Text } = Typography

const VAI_TRO_LABEL: Record<VaiTroThanhVien, string> = {
  CHU_TICH: 'Chủ tịch',
  THU_KY: 'Thư ký',
  UY_VIEN: 'Ủy viên',
}

/**
 * UC4.5/MH-02 "Lịch bảo vệ": bảng lịch (đề tài, thời gian, địa điểm, trạng
 * thái), thành viên hội đồng; điểm CHỈ hiện sau khi Bộ môn chốt (D-06 — server
 * không trả ket_qua trước đó).
 */
export default function MyDefensePage() {
  const { data, isLoading, isError, error } = useMyDefense()
  const { data: dashboard } = useSvDashboard()

  if (isLoading) {
    return (
      <Card title="Lịch bảo vệ">
        <Skeleton active />
      </Card>
    )
  }
  if (isError || !data) {
    return (
      <Card title="Lịch bảo vệ">
        <Alert type="error" showIcon message={getErrorMessage(error)} />
      </Card>
    )
  }
  if (!data.lich) {
    return (
      <Card title="Lịch bảo vệ">
        <Empty description="Bạn chưa được xếp lịch bảo vệ">
          <Link to="/de-cuong?tab=bao-cao-cuoi">Nộp báo cáo cuối</Link>
        </Empty>
      </Card>
    )
  }

  const lich = data.lich
  const daBaoVe = data.ket_qua !== null
  const row = {
    key: 1,
    ten_de_tai: dashboard?.de_tai?.ten_de_tai ?? '—',
    thoi_gian: `${formatDate(lich.ngay_bao_ve)} · ${lich.gio_du_kien}`,
    dia_diem: lich.phong,
  }

  return (
    <Card title="Lịch bảo vệ">
      <Table
        pagination={false}
        dataSource={[row]}
        columns={[
          { title: 'STT', key: 'stt', width: 60, render: () => 1 },
          { title: 'Tên đề tài', dataIndex: 'ten_de_tai' },
          { title: 'Thời gian bảo vệ', dataIndex: 'thoi_gian', width: 200 },
          { title: 'Địa điểm', dataIndex: 'dia_diem', width: 140 },
          {
            title: 'Trạng thái',
            key: 'trang_thai',
            width: 140,
            render: () => (daBaoVe ? <Tag color="success">Đã bảo vệ</Tag> : <Tag>Chưa đến</Tag>),
          },
        ]}
      />
      <div style={{ display: 'flex', gap: 48, marginTop: 20, flexWrap: 'wrap' }}>
        <div>
          <Text strong>{lich.ten_hoi_dong}</Text>
          <div style={{ marginTop: 8 }}>
            {lich.thanh_vien.map((m, idx) => (
              <div key={`${m.vai_tro}-${idx}`} style={{ marginBottom: 4 }}>
                {`${VAI_TRO_LABEL[m.vai_tro]}: ${[m.hoc_vi, m.ho_ten].filter(Boolean).join(' ')}`}
              </div>
            ))}
          </div>
        </div>
        <div>
          {data.ket_qua ? (
            <Statistic title="Điểm bảo vệ" value={data.ket_qua.diem_trung_binh} precision={2} />
          ) : (
            <div>
              <Text type="secondary">Điểm bảo vệ</Text>
              <div style={{ marginTop: 8 }}>
                <Tag>Chưa có kết quả</Tag>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
