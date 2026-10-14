import { Button, Card, Empty, Skeleton, Space, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link, useNavigate } from 'react-router'

import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { useMyStudents } from './api'
import type { MyStudentItem } from './api'

/**
 * MH-16/UC0.8: "Sinh viên của tôi" — lớp hướng dẫn Bộ môn phân công cho GV
 * trong các đợt đang mở, kèm đề tài hiện tại của từng SV. GV giao đề tài cho
 * SV chưa có đề tài ngay từ đây (mở form đề xuất với SV điền sẵn).
 */
export default function MyStudentsPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useMyStudents()

  if (isLoading) {
    return <Skeleton active />
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Sinh viên của tôi">
        <Empty description="Hiện không có đợt đồ án nào đang mở" />
      </Card>
    )
  }

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      {data.map((lop) => {
        const columns: ColumnsType<MyStudentItem> = [
          { title: 'Mã SV', key: 'ma', render: (_v, r) => r.sinh_vien.ma ?? '—', width: 140 },
          { title: 'Họ tên', key: 'ho_ten', render: (_v, r) => r.sinh_vien.ho_ten },
          { title: 'Lớp', dataIndex: 'lop', render: (v: string | null) => v ?? '—', width: 120 },
          { title: 'Email', dataIndex: 'email', render: (v: string | null) => v ?? '—' },
          {
            title: 'Đề tài',
            key: 'de_tai',
            render: (_v, r) =>
              r.de_tai_id ? (
                <Space size={4} wrap>
                  <Tag color={TRANG_THAI_DE_TAI[r.trang_thai_de_tai ?? '']?.color}>
                    {TRANG_THAI_DE_TAI[r.trang_thai_de_tai ?? '']?.label ?? r.trang_thai_de_tai}
                  </Tag>
                  <Link to={`/de-tai/${r.de_tai_id}`}>{r.ten_de_tai}</Link>
                </Space>
              ) : (
                <span style={{ color: 'rgba(0,0,0,0.45)' }}>Chưa có</span>
              ),
          },
          {
            title: 'Hành động',
            key: 'hanh_dong',
            width: 150,
            render: (_v, r) => {
              if (r.trang_thai_de_tai === 'CHO_DUYET') {
                return (
                  <Button size="small" type="primary" onClick={() => navigate(`/duyet-de-tai?de_tai_id=${r.de_tai_id}`)}>
                    Duyệt đề tài
                  </Button>
                )
              }
              const active = r.trang_thai_de_tai === 'DA_PHAN_CONG'
              return active ? null : (
                <Button
                  size="small"
                  onClick={() =>
                    navigate(`/de-tai/de-xuat?dot_do_an_id=${lop.dot_do_an.id}&sinh_vien_id=${r.sinh_vien.id}`)
                  }
                >
                  Giao đề tài
                </Button>
              )
            },
          },
        ]
        return (
          <Card
            key={lop.dot_do_an.id}
            title={`Sinh viên của tôi — ${lop.dot_do_an.ten_dot}`}
            extra={<span>{lop.items.length} sinh viên</span>}
          >
            <Table<MyStudentItem>
              rowKey={(r) => r.sinh_vien.id}
              columns={columns}
              dataSource={lop.items}
              pagination={false}
              locale={{ emptyText: 'Bộ môn chưa phân công sinh viên nào cho bạn trong đợt này' }}
            />
          </Card>
        )
      })}
    </Space>
  )
}
