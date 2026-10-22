import { useState } from 'react'
import { Button, Modal } from 'antd'
import type { ButtonProps } from 'antd'

import type { DocumentOut } from './api'
import FilePreview from './FilePreview'

/**
 * Nút "Xem" mở file đã nộp trong hộp thoại (FilePreview) — dùng ở lịch sử
 * phiên bản đề cương/báo cáo cuối và báo cáo tiến độ. Chặn sự kiện click lan
 * lên dòng chứa nút (MilestoneList chọn mốc khi bấm vào dòng; sự kiện trong
 * Modal cũng lan qua portal của React).
 */
export default function FilePreviewButton({
  doc,
  size = 'small',
  type,
}: {
  doc: DocumentOut
  size?: ButtonProps['size']
  type?: ButtonProps['type']
}) {
  const [open, setOpen] = useState(false)
  return (
    <span onClick={(e) => e.stopPropagation()}>
      <Button size={size} type={type} onClick={() => setOpen(true)}>
        Xem
      </Button>
      <Modal
        open={open}
        title={doc.ten_goc}
        width={1000}
        footer={null}
        destroyOnHidden
        onCancel={() => setOpen(false)}
      >
        <FilePreview doc={doc} height="75vh" />
      </Modal>
    </span>
  )
}
