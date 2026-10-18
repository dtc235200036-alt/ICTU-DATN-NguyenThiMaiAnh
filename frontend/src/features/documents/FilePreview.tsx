import { useEffect, useState } from 'react'
import { Alert, Empty, Spin, Typography } from 'antd'

import { api } from '../../api/client'
import type { DocumentOut } from './api'

/**
 * Xem trực tiếp file đã nộp: PDF hiển thị trong khung (blob qua API có xác
 * thực, không đặt token trên URL); DOCX hiển thị phần nội dung đã trích xuất.
 */
export default function FilePreview({ doc, height = 640 }: { doc: DocumentOut | undefined; height?: number }) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)
  const isPdf = doc?.dinh_dang === 'PDF'

  useEffect(() => {
    if (!doc || !isPdf) return undefined
    let objectUrl: string | null = null
    let cancelled = false
    setUrl(null)
    setError(false)
    api
      .get<Blob>(`/documents/${doc.id}/download`, { responseType: 'blob' })
      .then(({ data }) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
        setUrl(objectUrl)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [doc?.id, isPdf])

  if (!doc) return <Empty description="Chưa có file" />

  if (!isPdf) {
    return (
      <div>
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="File DOCX không xem trực tiếp được — dưới đây là phần đầu nội dung đã trích xuất; tải file để xem đầy đủ."
        />
        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
          {doc.tom_tat ?? '—'}
        </Typography.Paragraph>
      </div>
    )
  }
  if (error) return <Alert type="error" showIcon message="Không tải được file để xem" />
  if (!url) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin />
      </div>
    )
  }
  return (
    <iframe
      title={doc.ten_goc}
      src={url}
      style={{ width: '100%', height, border: '1px solid #f0f0f0', borderRadius: 6 }}
    />
  )
}
