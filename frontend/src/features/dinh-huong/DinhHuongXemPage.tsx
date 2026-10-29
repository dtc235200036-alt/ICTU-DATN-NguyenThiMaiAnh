import { Card, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import QueryErrorAlert from '../../components/QueryErrorAlert'
import { useDinhHuong } from './api'
import type { DinhHuongOut } from './api'
import TepMoTaButton from './TepMoTaButton'

const columns: ColumnsType<DinhHuongOut> = [
  { title: 'Mã', dataIndex: 'ma', width: 90 },
  { title: 'Tên định hướng', dataIndex: 'ten' },
  { title: 'Mô tả', dataIndex: 'mo_ta', render: (v: string | null) => v || '—' },
  {
    title: 'File mô tả',
    key: 'tep',
    width: 120,
    render: (_v, record) => (record.tep ? <TepMoTaButton dinhHuong={record} /> : '—'),
  },
]

/**
 * SV/GV xem danh mục định hướng đề tài đang sử dụng: mã, tên, mô tả và file
 * PDF mô tả do Bộ môn tải lên (xem ngay trên trình duyệt hoặc tải về).
 */
export default function DinhHuongXemPage() {
  const { data, isLoading, isError, error, refetch } = useDinhHuong(true)

  return (
    <Card title="Định hướng đề tài">
      <Typography.Paragraph type="secondary">
        Mã định hướng là phần đầu tên file đề cương: [Mã định hướng].[MSSV].[Họ tên].[Lớp].
      </Typography.Paragraph>
      {isError ? (
        <QueryErrorAlert error={error} onRetry={() => void refetch()} />
      ) : (
        <Table<DinhHuongOut>
          rowKey="id"
          loading={isLoading}
          columns={columns}
          dataSource={data ?? []}
          pagination={false}
        />
      )}
    </Card>
  )
}
