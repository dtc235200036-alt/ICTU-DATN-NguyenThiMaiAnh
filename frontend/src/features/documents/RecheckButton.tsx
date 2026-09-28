import { App as AntApp, Button } from 'antd'

import { getErrorMessage } from '../../api/client'
import { useRecheck } from './api'

/**
 * WR-13 (03-REVIEW): nút "Kiểm tra lại" dùng ở những nơi không có CheckPanel
 * (bảng lịch bảo vệ của Bộ môn, màn chấm điểm của hội đồng) — chỉ hiển thị
 * khi kết quả kiểm tra báo cáo cuối đang LOI (UC0.7). Server vẫn tự kiểm tra
 * quyền và trạng thái (409 nếu không còn LOI).
 */
export default function RecheckButton({ taiLieuId }: { taiLieuId: number }) {
  const { message } = AntApp.useApp()
  const recheckMutation = useRecheck()

  const handleClick = async () => {
    try {
      await recheckMutation.mutateAsync(taiLieuId)
      message.success('Đã yêu cầu kiểm tra lại')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  return (
    <Button size="small" loading={recheckMutation.isPending} onClick={() => void handleClick()}>
      Kiểm tra lại
    </Button>
  )
}
