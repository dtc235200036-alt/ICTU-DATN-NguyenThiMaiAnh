import { useEffect, useMemo, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Upload,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { UploadFile } from 'antd/es/upload/interface'

import { getErrorMessage } from '../../api/client'
import { formatBytes, formatDateTime } from '../../utils/format'
import { useMyProgress, useSubmitReport } from './api'
import type { MilestoneStatus } from './api'
import { DANH_GIA, TRANG_THAI_MOC, formatDay } from './constants'
import MilestoneList from './MilestoneList'

const { TextArea } = Input
const { Dragger } = Upload

// D-01/NFR-06: kiểm tra phía client chỉ để trải nghiệm — server kiểm tra lại
// theo magic bytes (cùng documents.read_and_validate với đề cương).
const MAX_SIZE_BYTES = 20 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.docx', '.pdf']
const NOI_DUNG_MAX = 10000

function canSubmitFor(m: MilestoneStatus): boolean {
  return m.bao_cao === null || m.bao_cao.nhan_xet === null
}

/**
 * MH-10 (phía SV)/UC3.2: danh sách mốc + form nộp báo cáo cho một mốc chưa
 * được GVHD nhận xét. Nộp lại trước khi nhận xét ghi đè nội dung (UC3.2 A1);
 * tệp đính kèm mới luôn thành một phiên bản tài liệu mới (D-02).
 */
export default function ProgressPage() {
  const { message } = AntApp.useApp()
  const { data, isLoading, isError, error } = useMyProgress()
  const submitMutation = useSubmitReport()

  const [mocId, setMocId] = useState<number | undefined>(undefined)
  const [noiDung, setNoiDung] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [fileError, setFileError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [viewing, setViewing] = useState<MilestoneStatus | null>(null)

  const topic = data?.de_tai ?? null
  const submittable = useMemo(() => (topic ? topic.moc.filter(canSubmitFor) : []), [topic])
  const selected = topic?.moc.find((m) => m.id === mocId)

  // Mặc định: mốc đầu tiên chưa nộp, nếu không có thì mốc đầu tiên còn nộp lại được.
  useEffect(() => {
    if (mocId !== undefined && submittable.some((m) => m.id === mocId)) return
    const first = submittable.find((m) => m.bao_cao === null) ?? submittable[0]
    setMocId(first?.id)
  }, [submittable, mocId])

  useEffect(() => {
    setNoiDung(selected?.bao_cao?.noi_dung ?? '')
    setFile(null)
    setFileList([])
    setFileError(null)
  }, [selected?.id, selected?.bao_cao?.id])

  if (isLoading) return <Spin />
  if (isError) return <Alert type="error" showIcon message={getErrorMessage(error)} />
  if (!topic) {
    return (
      <Card>
        <Empty description="Bạn chưa có đề tài được phân công GVHD" />
      </Card>
    )
  }

  const handleSelectFile = (candidate: File) => {
    const lower = candidate.name.toLowerCase()
    if (!ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
      setFileError(`"${candidate.name}" không phải DOCX hoặc PDF.`)
      return Upload.LIST_IGNORE
    }
    if (candidate.size > MAX_SIZE_BYTES) {
      setFileError(`"${candidate.name}" vượt quá dung lượng tối đa 20 MB (NFR-06).`)
      return Upload.LIST_IGNORE
    }
    setFileError(null)
    setFile(candidate)
    setFileList([
      { uid: '-1', name: candidate.name, status: 'done', size: candidate.size } as UploadFile,
    ])
    return false
  }

  const reset = () => {
    setNoiDung(selected?.bao_cao?.noi_dung ?? '')
    setFile(null)
    setFileList([])
    setFileError(null)
  }

  const handleSubmit = async () => {
    if (mocId === undefined) return
    const text = noiDung.trim()
    if (text.length === 0) {
      message.error('Vui lòng nhập nội dung công việc đã thực hiện')
      return
    }
    try {
      await submitMutation.mutateAsync({ mocId, noiDung: text, file: file ?? undefined })
      message.success(`Đã nộp báo cáo ${selected?.ten_moc ?? ''}`)
      setFormOpen(false)
      setFile(null)
      setFileList([])
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const disabled = !topic.co_the_nop || mocId === undefined
  const resubmitting = Boolean(selected?.bao_cao)

  const openForm = (m?: MilestoneStatus) => {
    if (m && canSubmitFor(m)) setMocId(m.id)
    setFormOpen(true)
  }

  const columns: ColumnsType<MilestoneStatus> = [
    { title: 'STT', key: 'stt', width: 60, render: (_v, _r, idx) => idx + 1 },
    { title: 'Tên báo cáo', dataIndex: 'ten_moc' },
    { title: 'Hạn nộp', dataIndex: 'han_nop', width: 110, render: (v: string | null) => formatDay(v) },
    {
      title: 'Thời gian nộp',
      key: 'thoi_diem_nop',
      width: 160,
      render: (_v, m) => (m.bao_cao ? formatDateTime(m.bao_cao.thoi_diem_nop) : '—'),
    },
    {
      title: 'Trạng thái',
      key: 'trang_thai',
      width: 150,
      render: (_v, m) => (
        <Space size={4} wrap>
          {m.bao_cao ? <Tag color="blue">Đã nộp</Tag> : null}
          <Tag color={TRANG_THAI_MOC[m.trang_thai].color}>{TRANG_THAI_MOC[m.trang_thai].label}</Tag>
        </Space>
      ),
    },
    {
      title: 'Đánh giá GVHD',
      key: 'danh_gia',
      width: 130,
      render: (_v, m) => {
        const dg = m.bao_cao?.danh_gia
        return dg ? <Tag color={DANH_GIA[dg].color}>{DANH_GIA[dg].label}</Tag> : '—'
      },
    },
    {
      title: 'Thao tác',
      key: 'thao_tac',
      width: 150,
      render: (_v, m) => (
        <Space size={4}>
          <Button size="small" disabled={!m.bao_cao} onClick={() => setViewing(m)}>
            Xem
          </Button>
          {topic.co_the_nop && canSubmitFor(m) && (
            <Button size="small" type="link" onClick={() => openForm(m)}>
              {m.bao_cao ? 'Nộp lại' : 'Nộp'}
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title={`Báo cáo tiến độ - ${topic.ten_de_tai}`}
      extra={
        <Space>
          {topic.tre_moc && <Tag color="red">Trễ mốc</Tag>}
          <Button type="primary" disabled={!topic.co_the_nop} onClick={() => openForm()}>
            + Tạo báo cáo mới
          </Button>
        </Space>
      }
    >
      {topic.ly_do && <Alert type="info" showIcon message={topic.ly_do} style={{ marginBottom: 16 }} />}
      <Table<MilestoneStatus>
        rowKey="id"
        columns={columns}
        dataSource={topic.moc}
        pagination={false}
        locale={{ emptyText: 'Bộ môn chưa thiết lập mốc tiến độ cho đợt này' }}
      />

      <Modal
        open={formOpen}
        title={`Nộp báo cáo tiến độ - ${selected?.ten_moc ?? ''}`}
        footer={null}
        width={640}
        onCancel={() => setFormOpen(false)}
      >
      {topic.ly_do && (
        <Alert type="info" showIcon message={topic.ly_do} style={{ marginBottom: 16 }} />
      )}
      <Form layout="vertical" disabled={disabled}>
        <Form.Item label="Mốc">
          <Select
            value={mocId}
            onChange={setMocId}
            options={submittable.map((m) => ({
              value: m.id,
              label: `${m.ten_moc} · hạn ${formatDay(m.han_nop)} · ${TRANG_THAI_MOC[m.trang_thai].label}`,
            }))}
            placeholder="Chọn mốc cần nộp"
          />
        </Form.Item>
        {resubmitting && (
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
            message="Mốc này đã nộp — nộp lại sẽ ghi đè nội dung (GVHD chưa nhận xét)."
          />
        )}
        <Form.Item label="Nội dung công việc đã thực hiện" required>
          <TextArea
            rows={6}
            maxLength={NOI_DUNG_MAX}
            showCount
            value={noiDung}
            onChange={(e) => setNoiDung(e.target.value)}
          />
        </Form.Item>
        <Form.Item label="Tệp đính kèm (tùy chọn)">
          {fileError && (
            <Alert type="error" showIcon message={fileError} style={{ marginBottom: 8 }} />
          )}
          <Dragger
            accept=".docx,.pdf"
            maxCount={1}
            multiple={false}
            fileList={fileList}
            beforeUpload={handleSelectFile}
            onRemove={() => {
              setFile(null)
              setFileList([])
            }}
          >
            <p className="ant-upload-text">Kéo thả file hoặc bấm để chọn (tùy chọn)</p>
            <p className="ant-upload-hint">DOCX hoặc PDF, tối đa 20 MB</p>
          </Dragger>
          {file && (
            <p style={{ marginTop: 8, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
              Đã chọn: {file.name} ({formatBytes(file.size)})
            </p>
          )}
        </Form.Item>
        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={reset}>Hủy</Button>
          <Button type="primary" loading={submitMutation.isPending} onClick={handleSubmit}>
            Nộp báo cáo
          </Button>
        </Space>
      </Form>
      </Modal>

      <Modal
        open={viewing !== null}
        title={viewing ? `Báo cáo ${viewing.ten_moc}` : ''}
        footer={null}
        width={640}
        onCancel={() => setViewing(null)}
      >
        {viewing && <MilestoneList moc={[viewing]} />}
      </Modal>
    </Card>
  )
}
