import { useState } from 'react'
import { Alert, Button, Upload } from 'antd'
import type { UploadFile } from 'antd/es/upload/interface'
import { AxiosError } from 'axios'

import { formatBytes } from '../../utils/format'

const { Dragger } = Upload

// D-01/NFR-06: giới hạn phía client chỉ để trải nghiệm — server luôn kiểm
// tra lại theo magic bytes (T-03-SC), đây không phải nguồn xác thực duy nhất.
const MAX_SIZE_BYTES = 20 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.docx', '.pdf']
const GENERIC_ERROR_DETAIL = 'Đã xảy ra lỗi. Vui lòng thử lại sau.'

interface UploadErrorState {
  title: string
  detail: string
}

export interface DocumentUploadProps {
  disabled: boolean
  disabledReason?: string
  submitLabel: string
  loading: boolean
  onSubmit: (file: File) => Promise<unknown>
}

function hasAllowedExtension(name: string): boolean {
  const lower = name.toLowerCase()
  return ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

function errorStateFrom(err: unknown): UploadErrorState {
  if (err instanceof AxiosError) {
    const status = err.response?.status
    const detail: unknown = err.response?.data?.detail
    const detailText = typeof detail === 'string' ? detail : GENERIC_ERROR_DETAIL
    if (status === 422) {
      return { title: 'Nộp thất bại: sai định dạng file', detail: detailText }
    }
    return { title: 'Nộp thất bại', detail: detailText }
  }
  return { title: 'Nộp thất bại', detail: GENERIC_ERROR_DETAIL }
}

/**
 * MH-08: khối "Nộp phiên bản mới" dùng chung bởi đề cương (03-02), báo cáo
 * tiến độ (03-03, đính kèm tùy chọn) và báo cáo cuối (03-04/UC4.1). Việc
 * nộp thật (mutateAsync + message.success) do trang gọi truyền vào qua
 * `onSubmit` — component này chỉ quản lý lựa chọn file + hiển thị lỗi.
 */
export default function DocumentUpload({
  disabled,
  disabledReason,
  submitLabel,
  loading,
  onSubmit,
}: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [clientError, setClientError] = useState<string | null>(null)
  const [serverError, setServerError] = useState<UploadErrorState | null>(null)

  const clearSelection = () => {
    setFile(null)
    setFileList([])
  }

  const handleSelect = (candidate: File) => {
    setServerError(null)
    if (!hasAllowedExtension(candidate.name)) {
      setClientError(`"${candidate.name}" không phải DOCX hoặc PDF.`)
      clearSelection()
      return false
    }
    if (candidate.size > MAX_SIZE_BYTES) {
      setClientError(`"${candidate.name}" vượt quá dung lượng tối đa 20 MB (NFR-06).`)
      clearSelection()
      return false
    }
    setClientError(null)
    setFile(candidate)
    setFileList([
      { uid: '-1', name: candidate.name, status: 'done', size: candidate.size } as UploadFile,
    ])
    // false: không tự upload theo cơ chế mặc định của antd — trang gọi
    // onSubmit (multipart qua axios) khi bấm nút, không phải khi chọn file.
    return false
  }

  const handleSubmit = async () => {
    if (!file) return
    setServerError(null)
    try {
      await onSubmit(file)
      clearSelection()
    } catch (err) {
      setServerError(errorStateFrom(err))
    }
  }

  return (
    <div>
      {disabled && disabledReason && (
        <Alert type="info" showIcon message={disabledReason} style={{ marginBottom: 16 }} />
      )}
      {serverError && (
        <Alert
          type="error"
          showIcon
          message={serverError.title}
          description={serverError.detail}
          style={{ marginBottom: 16 }}
        />
      )}
      {clientError && (
        <Alert type="error" showIcon message={clientError} style={{ marginBottom: 16 }} />
      )}
      <Dragger
        accept=".docx,.pdf"
        maxCount={1}
        multiple={false}
        disabled={disabled}
        fileList={fileList}
        beforeUpload={handleSelect}
        onRemove={() => {
          clearSelection()
          setClientError(null)
        }}
      >
        <p className="ant-upload-text">Kéo thả file vào đây hoặc bấm để chọn file</p>
        <p className="ant-upload-hint">Chỉ nhận DOCX hoặc PDF, tối đa 20 MB (NFR-06)</p>
      </Dragger>
      {file && (
        <p style={{ marginTop: 8, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
          Đã chọn: {file.name} ({formatBytes(file.size)})
        </p>
      )}
      <Button
        type="primary"
        block
        style={{ marginTop: 16 }}
        disabled={disabled || !file}
        loading={loading}
        onClick={handleSubmit}
      >
        {submitLabel}
      </Button>
    </div>
  )
}
