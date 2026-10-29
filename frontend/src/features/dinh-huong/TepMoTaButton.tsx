import { useState } from 'react'
import { App as AntApp, Button, Modal } from 'antd'
import type { ButtonProps } from 'antd'

import { DownloadError, downloadFile } from '../../api/download'
import { PdfBlobView } from '../documents/FilePreview'
import { dinhHuongLabel, tepDinhHuongPath } from './api'
import type { DinhHuongOut } from './api'

/**
 * Nút "Xem" mở file PDF mô tả định hướng trong hộp thoại (PdfBlobView — tải
 * qua API có xác thực, không đặt token trên URL), kèm nút tải về. Không hiện
 * gì khi định hướng chưa có file.
 */
export default function TepMoTaButton({
  dinhHuong,
  label = 'Xem',
  size = 'small',
  type,
}: {
  dinhHuong: DinhHuongOut
  label?: string
  size?: ButtonProps['size']
  type?: ButtonProps['type']
}) {
  const { message } = AntApp.useApp()
  const [open, setOpen] = useState(false)
  const tep = dinhHuong.tep
  if (!tep) return null

  const handleDownload = () => {
    downloadFile(tepDinhHuongPath(dinhHuong.id), tep.ten_goc).catch((err: unknown) =>
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file'),
    )
  }

  return (
    <span onClick={(e) => e.stopPropagation()}>
      <Button size={size} type={type} onClick={() => setOpen(true)}>
        {label}
      </Button>
      <Modal
        open={open}
        title={`${dinhHuongLabel(dinhHuong)} — ${tep.ten_goc}`}
        width={1000}
        destroyOnHidden
        onCancel={() => setOpen(false)}
        footer={[
          <Button key="tai-ve" onClick={handleDownload}>
            ⬇ Tải về
          </Button>,
          <Button key="dong" type="primary" onClick={() => setOpen(false)}>
            Đóng
          </Button>,
        ]}
      >
        <PdfBlobView path={tepDinhHuongPath(dinhHuong.id)} title={tep.ten_goc} height="75vh" />
      </Modal>
    </span>
  )
}
