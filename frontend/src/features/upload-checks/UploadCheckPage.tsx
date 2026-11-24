import { Alert, Card, Table } from 'antd'
import { Link, useNavigate } from 'react-router'

import { formatDateTime, formatPercent } from '../../utils/format'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import CheckStatusTag from '../documents/CheckStatusTag'
import DocumentUpload from '../documents/DocumentUpload'
import { useCreateUploadCheck, useUploadChecks } from './api'
import type { UploadCheckSummary } from './api'

/** 0020: tải một tệp PDF/DOCX lên để kiểm tra trùng lặp với kho đồ án. */
export default function UploadCheckPage() {
  const navigate = useNavigate()
  const create = useCreateUploadCheck()
  const history = useUploadChecks()

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 20px' }}>Kiểm tra đạo văn</h1>

      <Card style={{ marginBottom: 20 }}>
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="Tệp được so sánh với kho đồ án và các tài liệu đã nộp trong hệ thống."
          description="Tệp chỉ dùng cho lần kiểm tra này: không được lưu và không được thêm vào kho, nên không ảnh hưởng tới kết quả kiểm tra của sinh viên. Đồ án dài có thể mất vài phút."
        />
        <DocumentUpload
          disabled={false}
          submitLabel="Kiểm tra"
          loading={create.isPending}
          onSubmit={async (file) => {
            const ketQua = await create.mutateAsync(file)
            navigate(`/kiem-tra-dao-van/${ketQua.id}`)
          }}
        />
      </Card>

      <Card title="Các lần kiểm tra gần đây">
        {history.isError ? (
          <QueryErrorAlert error={history.error} />
        ) : (
          <Table<UploadCheckSummary>
            rowKey="id"
            size="small"
            loading={history.isLoading}
            dataSource={history.data ?? []}
            pagination={false}
            locale={{ emptyText: 'Chưa kiểm tra tệp nào' }}
            columns={[
              {
                title: 'Tệp',
                dataIndex: 'ten_tep',
                render: (ten: string, row) => <Link to={`/kiem-tra-dao-van/${row.id}`}>{ten}</Link>,
              },
              { title: 'Thời điểm', dataIndex: 'thoi_diem', render: (v: string) => formatDateTime(v) },
              { title: 'Kết quả', key: 'trang_thai', render: (_, row) => <CheckStatusTag kiemTra={row} /> },
              {
                title: 'Trùng nhiều nhất với một đồ án',
                dataIndex: 'ty_le_nguon_cao_nhat',
                render: (v: number | null) => formatPercent(v),
              },
            ]}
          />
        )}
      </Card>
    </div>
  )
}
