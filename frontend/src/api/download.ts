import { AxiosError } from 'axios'

import { api } from './client'

// D-02: tải file DUY NHẤT qua endpoint có Authorization header (axios
// interceptor tự gắn Bearer) — không bao giờ đặt token trên URL hay dùng
// đường dẫn tĩnh. responseType 'blob' để có bytes gốc cho createObjectURL.
const GENERIC_ERROR_MESSAGE = 'Đã xảy ra lỗi. Vui lòng thử lại sau.'

/** Lỗi tải file: message đã được trích từ JSON `detail` của server (khi có),
 * sẵn sàng hiển thị trực tiếp bằng `message.error(err.message)`. */
export class DownloadError extends Error {}

function parseFilenameFromContentDisposition(
  header: string | undefined,
  fallbackName: string,
): string {
  if (!header) return fallbackName
  const starMatch = /filename\*\s*=\s*utf-8''([^;]+)/i.exec(header)
  if (starMatch) {
    try {
      return decodeURIComponent(starMatch[1])
    } catch {
      // rơi xuống các cách khác nếu chuỗi percent-encode không hợp lệ
    }
  }
  const plainMatch = /filename\s*=\s*"([^"]*)"/i.exec(header)
  if (plainMatch) {
    return plainMatch[1]
  }
  return fallbackName
}

async function extractBlobErrorMessage(blob: Blob): Promise<string> {
  try {
    const text = await blob.text()
    const parsed = JSON.parse(text) as { detail?: unknown }
    if (typeof parsed.detail === 'string') {
      return parsed.detail
    }
  } catch {
    // body không phải JSON hợp lệ — dùng thông điệp chung
  }
  return GENERIC_ERROR_MESSAGE
}

/**
 * Tải một file qua API đã xác thực rồi kích hoạt tải xuống trình duyệt.
 * `path` là đường dẫn tương đối dưới `/api` (vd. `/documents/{id}/download`).
 * `fallbackName` dùng khi server không trả Content-Disposition phân tích được.
 */
export async function downloadFile(path: string, fallbackName: string): Promise<void> {
  let blob: Blob
  let contentDisposition: string | undefined
  try {
    const response = await api.get<Blob>(path, { responseType: 'blob' })
    blob = response.data
    contentDisposition = response.headers['content-disposition'] as string | undefined
  } catch (err) {
    if (err instanceof AxiosError && err.response?.data instanceof Blob) {
      const message = await extractBlobErrorMessage(err.response.data)
      throw new DownloadError(message)
    }
    throw err
  }

  const filename = parseFilenameFromContentDisposition(contentDisposition, fallbackName)
  const url = URL.createObjectURL(blob)
  try {
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}
