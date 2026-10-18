import { Button, Card, Skeleton, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router'

import QueryErrorAlert from '../../components/QueryErrorAlert'
import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { isAppPath } from '../notifications/api'
import { useGvDashboard } from './api'
import type { GvTaskItem, GvTopicItem, LoaiViec } from './api'

const LOAI_VIEC: Record<LoaiViec, { label: string; color: string; action: string }> = {
  GIAO_DE_TAI: { label: 'Giao đề tài', color: 'cyan', action: 'Giao' },
  DUYET_DE_CUONG: { label: 'Duyệt đề cương', color: 'blue', action: 'Duyệt' },
  NOP_DE_CUONG_BO_MON: { label: 'Nộp đề cương lên Bộ môn', color: 'geekblue', action: 'Nộp' },
  NHAN_XET_TIEN_DO: { label: 'Nhận xét tiến độ', color: 'gold', action: 'Xem' },
  CHAM_DIEM: { label: 'Chấm điểm bảo vệ', color: 'purple', action: 'Chấm điểm' },
}

/** MH-03: chỉ số + "Việc cần xử lý" (giao đề tài, đề cương, tiến độ, chấm điểm) + đề tài của GV. */
export default function GvDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, error, refetch } = useGvDashboard()

  const columns: ColumnsType<GvTopicItem> = [
    { title: 'Tên đề tài', dataIndex: 'ten_de_tai' },
    { title: 'Sinh viên', dataIndex: 'sinh_vien', render: (value: string | null) => value ?? '—' },
    {
      title: 'Trạng thái',
      dataIndex: 'trang_thai',
      render: (value: string) => {
        const meta = TRANG_THAI_DE_TAI[value] ?? { label: value, color: 'default' }
        return <Tag color={meta.color}>{meta.label}</Tag>
      },
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => <a onClick={() => navigate(`/de-tai/${record.id}`)}>Xem</a>,
    },
  ]

  const taskColumns: ColumnsType<GvTaskItem> = [
    {
      title: 'Loại việc',
      dataIndex: 'loai',
      width: 180,
      render: (value: LoaiViec) => <Tag color={LOAI_VIEC[value].color}>{LOAI_VIEC[value].label}</Tag>,
    },
    {
      title: 'Sinh viên / Đề tài',
      key: 'sv',
      render: (_v, r) =>
        r.sinh_vien === null && r.ten_de_tai === null
          ? 'Lớp hướng dẫn'
          : `${r.sinh_vien ?? '—'} - ${r.ten_de_tai ?? '—'}`,
    },
    { title: 'Hạn / Ghi chú', dataIndex: 'ghi_chu' },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      width: 130,
      render: (_v, r) => (
        <Button
          size="small"
          type={r.loai === 'NHAN_XET_TIEN_DO' ? 'default' : 'primary'}
          onClick={() => {
            if (isAppPath(r.lien_ket)) navigate(r.lien_ket)
          }}
        >
          {LOAI_VIEC[r.loai].action}
        </Button>
      ),
    },
  ]

  if (isError) {
    return (
      <Card>
        <QueryErrorAlert error={error} onRetry={() => void refetch()} />
      </Card>
    )
  }

  if (isLoading || !data) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
        <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/sinh-vien-huong-dan')}>
          <Statistic title="Sinh viên trong lớp" value={data.so_sinh_vien_lop} />
        </Card>
        <Card style={{ minWidth: 220 }}>
          <Statistic
            title="Sinh viên hướng dẫn"
            value={data.so_sinh_vien_huong_dan}
            suffix={`/ ${data.so_de_tai} đề tài`}
          />
        </Card>
        <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/sinh-vien-huong-dan')}>
          <Statistic
            title="SV chưa được giao đề tài"
            value={data.so_sinh_vien_chua_giao_de_tai}
            valueStyle={data.so_sinh_vien_chua_giao_de_tai > 0 ? { color: '#cf1322' } : undefined}
          />
        </Card>
        <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/duyet-de-cuong')}>
          <Statistic title="Đề cương chờ duyệt" value={data.so_de_cuong_cho_duyet} />
        </Card>
        <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/nhan-xet-tien-do')}>
          <Statistic title="Báo cáo tiến độ chờ nhận xét" value={data.so_bao_cao_cho_nhan_xet} />
        </Card>
        <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/cham-diem')}>
          <Statistic title="Hội đồng tham gia" value={data.so_hoi_dong_tham_gia} />
        </Card>
      </div>

      <Card title="Việc cần xử lý" style={{ marginBottom: 20 }}>
        <Table<GvTaskItem>
          rowKey={(r) => `${r.lien_ket}#${r.ghi_chu}`}
          columns={taskColumns}
          dataSource={data.viec_can_xu_ly}
          pagination={false}
          locale={{ emptyText: 'Không có việc cần xử lý' }}
        />
      </Card>

      <Card title="Đề tài hướng dẫn">
        <Table<GvTopicItem>
          rowKey="id"
          columns={columns}
          dataSource={data.de_tai}
          pagination={false}
          locale={{ emptyText: 'Chưa có đề tài' }}
        />
      </Card>
    </div>
  )
}
