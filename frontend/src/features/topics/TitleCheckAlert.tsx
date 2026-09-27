import { Alert, Button, Progress, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import type { TitleCheckResult, TitleMatch } from './api'

interface TitleCheckAlertProps {
  result: TitleCheckResult
  onEditTitle: () => void
  onSendAnyway: () => void
}

const columns: ColumnsType<TitleMatch> = [
  { title: 'Tên đề tài', dataIndex: 'ten_de_tai' },
  { title: 'Khóa', dataIndex: 'khoa' },
  { title: 'GVHD', dataIndex: 'giang_vien', render: (v: string | null) => v ?? '—' },
  {
    title: 'Tỷ lệ tương đồng',
    dataIndex: 'ty_le',
    render: (ty_le: number) => <Progress percent={ty_le} size="small" />,
  },
]

/**
 * MH-06 (UC0.6/FR-DT-02): cảnh báo đề tài tương tự trước khi gửi đề xuất —
 * KHÔNG BAO GIỜ chặn việc gửi, chỉ cảnh báo (UC1.1 A1/A2). Khi Dịch vụ AI lỗi
 * (E2), hiển thị thông báo "Chưa kiểm tra" thay vì bảng so sánh.
 */
export default function TitleCheckAlert({
  result,
  onEditTitle,
  onSendAnyway,
}: TitleCheckAlertProps) {
  if (result.trang_thai === 'LOI') {
    return (
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Chưa kiểm tra được trùng lặp tên đề tài (dịch vụ kiểm tra không phản hồi). Bạn vẫn có thể gửi đề xuất; Bộ môn sẽ thấy trạng thái Chưa kiểm tra."
      />
    )
  }

  if (result.matches.length === 0) {
    return null
  }

  return (
    <Alert
      type="warning"
      showIcon
      style={{ marginBottom: 16 }}
      message={`Phát hiện ${result.matches.length} đề tài tương tự trong kho`}
      description={
        <div>
          <p>
            Hệ thống so sánh ngữ nghĩa tên đề tài với kho đề tài các khóa trước. Đây chỉ là
            cảnh báo, không chặn việc gửi đề xuất.
          </p>
          <Table<TitleMatch>
            size="small"
            rowKey="de_tai_id"
            pagination={false}
            columns={columns}
            dataSource={result.matches}
            style={{ marginBottom: 12 }}
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <Button size="small" onClick={onEditTitle}>
              Sửa tên đề tài
            </Button>
            <Button size="small" type="primary" onClick={onSendAnyway}>
              Vẫn gửi đề xuất
            </Button>
          </div>
        </div>
      }
    />
  )
}
