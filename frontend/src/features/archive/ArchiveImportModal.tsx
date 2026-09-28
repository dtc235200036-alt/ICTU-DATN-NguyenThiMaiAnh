import { useState } from 'react'
import { App as AntApp, Alert, Button, Modal, Table, Upload } from 'antd'
import type { UploadFile } from 'antd/es/upload/interface'

import { getErrorMessage } from '../../api/client'
import { useImportArchive } from './api'
import type { ImportResult, ImportRowError } from './api'

const CSV_COLUMNS =
  'khoa*, ten_de_tai*, ma_so_sinh_vien, ho_ten_sinh_vien, ma_giang_vien, tu_khoa, diem'
const CSV_EXAMPLE =
  'K19,Xây dựng hệ thống quản lý thư viện số,DTC195200011,Trần Văn Bình,GV001,"thư viện, quản lý",8.5'

export interface ArchiveImportModalProps {
  open: boolean
  onClose: () => void
}

/**
 * UC5.4 (MH-13): Bộ môn import đồ án khóa cũ từ CSV (định dạng ghi trong
 * deploy/README.md). Import thành công một phần: dòng lỗi được liệt kê kèm số
 * dòng + lý do (UC5.4 E1), các dòng hợp lệ đã lưu và được index nền.
 */
export default function ArchiveImportModal({ open, onClose }: ArchiveImportModalProps) {
  const { message } = AntApp.useApp()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [result, setResult] = useState<ImportResult | null>(null)
  const importMutation = useImportArchive()

  const close = () => {
    setFileList([])
    setResult(null)
    onClose()
  }

  const handleImport = async () => {
    const file = fileList[0]?.originFileObj
    if (!file) return
    try {
      setResult(await importMutation.mutateAsync(file))
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  return (
    <Modal
      open={open}
      title="Import đồ án khóa cũ"
      onCancel={close}
      width={640}
      footer={[
        <Button key="close" onClick={close}>
          Đóng
        </Button>,
        <Button
          key="import"
          type="primary"
          disabled={fileList.length === 0}
          loading={importMutation.isPending}
          onClick={handleImport}
        >
          Import
        </Button>,
      ]}
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="File CSV (UTF-8, tối đa 2 MB / 2000 dòng), dòng đầu là tiêu đề cột"
        description={
          <div>
            <div>Các cột (* bắt buộc): {CSV_COLUMNS}</div>
            <div style={{ marginTop: 4 }}>Ví dụ một dòng:</div>
            <code style={{ display: 'block', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {CSV_EXAMPLE}
            </code>
            <div style={{ marginTop: 4 }}>
              Điểm 0–10 (8.5 hoặc 8,5); mã giảng viên phải đã có trong hệ thống; dòng trùng
              khóa + tên đề tài bị bỏ qua.
            </div>
          </div>
        }
      />
      <Upload
        accept=".csv"
        maxCount={1}
        fileList={fileList}
        beforeUpload={() => false}
        onChange={({ fileList: next }) => {
          setFileList(next.slice(-1))
          setResult(null)
        }}
      >
        <Button>Chọn file CSV</Button>
      </Upload>

      {result && (
        <div style={{ marginTop: 16 }}>
          <Alert
            type={result.loi.length === 0 ? 'success' : 'warning'}
            showIcon
            message={`Đã nhập ${result.thanh_cong}/${result.tong_dong} dòng`}
            style={{ marginBottom: result.loi.length > 0 ? 12 : 0 }}
          />
          {result.loi.length > 0 && (
            <Table<ImportRowError>
              size="small"
              rowKey="dong"
              pagination={result.loi.length > 10 ? { pageSize: 10 } : false}
              dataSource={result.loi}
              columns={[
                { title: 'Dòng', dataIndex: 'dong', width: 80 },
                { title: 'Lý do', dataIndex: 'ly_do' },
              ]}
            />
          )}
        </div>
      )}
    </Modal>
  )
}
