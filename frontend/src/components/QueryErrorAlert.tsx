import type { CSSProperties } from 'react'
import { Alert, Button } from 'antd'

import { getErrorMessage } from '../api/client'

export interface QueryErrorAlertProps {
  error: unknown
  onRetry?: () => void
  style?: CSSProperties
}

/**
 * WR-12 (03-REVIEW): lỗi tải dữ liệu phải hiện là lỗi (kèm "Thử lại"), không
 * được rơi vào trạng thái rỗng ("chưa có ...") hay skeleton vô tận.
 */
export default function QueryErrorAlert({ error, onRetry, style }: QueryErrorAlertProps) {
  return (
    <Alert
      type="error"
      showIcon
      message="Không tải được dữ liệu"
      description={getErrorMessage(error)}
      style={style}
      action={
        onRetry ? (
          <Button size="small" onClick={onRetry}>
            Thử lại
          </Button>
        ) : undefined
      }
    />
  )
}
