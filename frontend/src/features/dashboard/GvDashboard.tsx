import { Card, Skeleton, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router'

import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { useGvDashboard } from './api'
import type { GvTopicItem } from './api'

/** MH-03 (subset Phase 2): số SV hướng dẫn/đề tài chờ duyệt + bảng đề tài của GV. */
export default function GvDashboard() {
  const navigate = useNavigate()
  const { data, isLoading } = useGvDashboard()

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
        <Card style={{ minWidth: 220 }}>
          <Statistic
            title="Sinh viên hướng dẫn"
            value={data.so_sinh_vien_huong_dan}
            suffix={`/ ${data.so_de_tai} đề tài`}
          />
        </Card>
        <Card style={{ minWidth: 220 }}>
          <Statistic title="Đề tài chờ duyệt" value={data.so_de_tai_cho_duyet} />
        </Card>
      </div>

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
