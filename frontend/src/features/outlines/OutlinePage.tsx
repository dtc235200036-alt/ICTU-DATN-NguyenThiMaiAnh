import { useState } from 'react'
import { App as AntApp, Button, Card, Empty, Skeleton, Table, Tag, Upload } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import { formatBytes, formatDate } from '../../utils/format'
import { useOutline, useOutlines, useSubmitOutline } from './api'
import type { OutlineVersion } from './api'

const { Dragger } = Upload

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

function renderKiemTra(version: OutlineVersion) {
  if (!version.kiem_tra || version.kiem_tra.trang_thai === 'DANG_KIEM_TRA') {
    return (
      <span style={{ color: 'rgba(0,0,0,0.45)' }}>
        {version.kiem_tra ? 'Đang kiểm tra' : 'Chưa có kết quả'}
      </span>
    )
  }
  if (version.kiem_tra.trang_thai === 'HOAN_TAT') {
    return <Tag color="success">{`Hoàn tất - ${version.kiem_tra.ty_le_tong ?? 0}%`}</Tag>
  }
  return <Tag color="error">Lỗi kiểm tra</Tag>
}

/**
 * MH-08 (tracer, thin — fidelity đầy đủ ở plan 03-02): SV nộp phiên bản mới
 * bằng Upload.Dragger và xem lịch sử phiên bản đề cương của đề tài mình.
 */
export default function OutlinePage() {
  const { message } = AntApp.useApp()
  const [file, setFile] = useState<File | null>(null)

  const { data: outlinesPage, isLoading: isListLoading } = useOutlines({})
  const ownItem = outlinesPage?.items[0]
  const deTaiId = ownItem?.de_tai_id

  const { data: detail, isLoading: isDetailLoading } = useOutline(deTaiId)
  const submitMutation = useSubmitOutline()

  if (isListLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  if (!ownItem || deTaiId === undefined) {
    return (
      <Card>
        <Empty description="Bạn chưa có đề tài được phân công GVHD" />
      </Card>
    )
  }

  if (isDetailLoading || !detail) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  const trangThai = TRANG_THAI_LABEL[detail.trang_thai] ?? {
    label: detail.trang_thai,
    color: 'default',
  }

  const handleSubmit = async () => {
    if (!file) return
    try {
      await submitMutation.mutateAsync({ deTaiId, file })
      message.success('Đã nộp đề cương')
      setFile(null)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<OutlineVersion> = [
    {
      title: 'Phiên bản',
      key: 'phien_ban',
      render: (_value, record) => `v${record.tai_lieu.so_phien_ban}`,
    },
    {
      title: 'Ngày nộp',
      key: 'ngay_nop',
      render: (_value, record) => formatDate(record.tai_lieu.thoi_diem_nop),
    },
    {
      title: 'Trạng thái duyệt',
      key: 'trang_thai_duyet',
      render: (_value, record) =>
        record.luot_duyet ? (
          <Tag color={record.luot_duyet.ket_qua === 'DA_DUYET' ? 'success' : 'error'}>
            {record.luot_duyet.ket_qua === 'DA_DUYET' ? 'Đã duyệt' : 'Yêu cầu sửa'}
          </Tag>
        ) : (
          <Tag color="processing">Chờ duyệt</Tag>
        ),
    },
    {
      title: 'Kết quả kiểm tra',
      key: 'kiem_tra',
      render: (_value, record) => renderKiemTra(record),
    },
  ]

  return (
    <Card title={detail.ten_de_tai} extra={<Tag color={trangThai.color}>{trangThai.label}</Tag>}>
      <Card size="small" title="Nộp phiên bản mới" style={{ marginBottom: 20 }}>
        <Dragger
          accept=".docx,.pdf"
          maxCount={1}
          multiple={false}
          disabled={!detail.quyen.nop}
          beforeUpload={(f) => {
            setFile(f)
            return false
          }}
          onRemove={() => setFile(null)}
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
          disabled={!detail.quyen.nop || !file}
          loading={submitMutation.isPending}
          onClick={handleSubmit}
        >
          Nộp phiên bản mới
        </Button>
      </Card>

      <Table<OutlineVersion>
        size="small"
        rowKey={(record) => record.tai_lieu.id}
        columns={columns}
        dataSource={detail.phien_ban}
        pagination={false}
        locale={{ emptyText: 'Chưa có phiên bản nào' }}
      />
    </Card>
  )
}
