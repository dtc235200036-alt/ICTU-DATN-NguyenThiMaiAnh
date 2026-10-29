import { useEffect, useRef, useState } from 'react'
import { Alert, Empty, Spin, Typography } from 'antd'
import type { Options as DocxOptions } from 'docx-preview'

import { api } from '../../api/client'
import type { DocumentOut } from './api'

type PreviewHeight = number | string

const FRAME_STYLE = { width: '100%', border: '1px solid #f0f0f0', borderRadius: 6 }

// Ảnh và phông nhúng dạng data: (CSP img-src/font-src không cho blob:); không
// hiển thị bình luận, vết sửa và khối HTML nhúng (altChunk) của người nộp.
const DOCX_OPTIONS: Partial<DocxOptions> = {
  inWrapper: true,
  breakPages: true,
  ignoreLastRenderedPageBreak: true,
  useBase64URL: true,
  renderComments: false,
  renderChanges: false,
  renderAltChunks: false,
}

function fetchFile(path: string): Promise<Blob> {
  return api.get<Blob>(path, { responseType: 'blob' }).then(({ data }) => data)
}

function downloadPath(id: number): string {
  return `/documents/${id}/download`
}

/** Liên kết trong DOCX do người nộp đặt: chỉ giữ liên kết nội bộ (#...) và
 * http(s)/mailto (mở tab mới), bỏ mọi giao thức khác (javascript:...). */
function sanitizeLinks(root: HTMLElement) {
  root.querySelectorAll('a[href]').forEach((a) => {
    const href = a.getAttribute('href') ?? ''
    if (href.startsWith('#')) return
    if (/^(https?:|mailto:)/i.test(href)) {
      a.setAttribute('target', '_blank')
      a.setAttribute('rel', 'noopener noreferrer')
    } else {
      a.removeAttribute('href')
    }
  })
}

/** Thu nhỏ trang DOCX (khổ A4 ≈ 794 px) cho vừa chiều rộng khung, không phóng
 * to. Đo theo trang rộng nhất chứ không theo scrollWidth: wrapper căn giữa
 * trang (flex), phần tràn sang trái không được tính vào scrollWidth. */
function fitWidth(host: HTMLElement, width: number) {
  const wrapper = host.querySelector<HTMLElement>('.docx-wrapper')
  if (!wrapper || width <= 0) return
  wrapper.style.zoom = '1'
  const style = getComputedStyle(wrapper)
  const pages = Array.from(wrapper.querySelectorAll<HTMLElement>(':scope > section'), (s) => s.offsetWidth)
  const needed = Math.max(0, ...pages) + parseFloat(style.paddingLeft) + parseFloat(style.paddingRight)
  if (needed > 0) wrapper.style.zoom = String(Math.min(1, width / needed))
}

/**
 * Xem một file PDF lấy qua API có xác thực (`path` dưới `/api`, vd.
 * `/documents/{id}/download`, `/dinh-huong/{id}/tep`): tải về dạng blob rồi
 * hiển thị qua object URL trong khung PDF của trình duyệt (CSP cho phép
 * frame-src blob:).
 */
export function PdfBlobView({
  path,
  title,
  height = 640,
}: {
  path: string
  title: string
  height?: PreviewHeight
}) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let objectUrl: string | null = null
    let cancelled = false
    setUrl(null)
    setError(false)
    fetchFile(path)
      .then((data) => {
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
  }, [path])

  if (error) return <Alert type="error" showIcon message="Không tải được file để xem" />
  if (!url) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin />
      </div>
    )
  }
  return <iframe title={title} src={url} style={{ ...FRAME_STYLE, height }} />
}

function DocxView({ doc, height }: { doc: DocumentOut; height: PreviewHeight }) {
  const frameRef = useRef<HTMLDivElement>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    const frame = frameRef.current
    if (!frame) return undefined
    // Mỗi lần render một khung con riêng: bản render của file cũ còn dở dang
    // không ghi đè được file mới (đổi phiên bản nhanh).
    const host = document.createElement('div')
    frame.appendChild(host)
    let cancelled = false
    let observer: ResizeObserver | undefined
    setStatus('loading')
    Promise.all([fetchFile(downloadPath(doc.id)), import('docx-preview')])
      .then(async ([data, { renderAsync }]) => {
        if (cancelled) return
        await renderAsync(data, host, undefined, DOCX_OPTIONS)
        if (cancelled) return
        sanitizeLinks(host)
        const wrapper = host.querySelector<HTMLElement>('.docx-wrapper')
        if (wrapper) {
          wrapper.style.background = 'transparent'
          wrapper.style.padding = '16px 16px 0'
        }
        fitWidth(host, frame.clientWidth)
        observer = new ResizeObserver(() => fitWidth(host, frame.clientWidth))
        observer.observe(frame)
        setStatus('ready')
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
      observer?.disconnect()
      host.remove()
    }
  }, [doc.id])

  return (
    <div>
      {status === 'error' && (
        <div>
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 12 }}
            message="Không hiển thị được file DOCX này — dưới đây là phần đầu nội dung đã trích xuất; tải file để xem đầy đủ."
          />
          <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
            {doc.tom_tat ?? '—'}
          </Typography.Paragraph>
        </div>
      )}
      <div
        ref={frameRef}
        style={{
          ...FRAME_STYLE,
          height,
          overflow: 'auto',
          background: '#f5f5f5',
          position: 'relative',
          display: status === 'error' ? 'none' : undefined,
        }}
      >
        {status === 'loading' && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="Đang mở file DOCX…">
              <div style={{ height: 40 }} />
            </Spin>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Xem trực tiếp file đã nộp, tải qua API có xác thực (không đặt token trên
 * URL): PDF hiển thị trong khung của trình duyệt; DOCX được dựng lại thành
 * các trang ngay trên trình duyệt bằng docx-preview (nạp khi cần).
 */
export default function FilePreview({ doc, height = 640 }: { doc: DocumentOut | undefined; height?: PreviewHeight }) {
  if (!doc) return <Empty description="Chưa có file" />
  return doc.dinh_dang === 'PDF' ? (
    <PdfBlobView key={doc.id} path={downloadPath(doc.id)} title={doc.ten_goc} height={height} />
  ) : (
    <DocxView key={doc.id} doc={doc} height={height} />
  )
}
