import { useState } from 'react'
import {
  App as AntApp,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import { formatBytes, formatDateTime } from '../../utils/format'
import {
  useDeleteTepDinhHuong,
  useDinhHuong,
  useSaveDinhHuong,
  useUploadTepDinhHuong,
} from './api'
import type { DinhHuongInput, DinhHuongOut } from './api'
import TepMoTaButton from './TepMoTaButton'

// Giới hạn phía client chỉ để trải nghiệm — server kiểm tra lại đuôi, magic
// bytes và dung lượng (cùng mức 20 MB với các file nộp khác).
const MAX_TEP_BYTES = 20 * 1024 * 1024

/**
 * Bộ môn quản lý danh mục định hướng đề tài (thay cho "Lĩnh vực"). Mã định
 * hướng là phần đầu tên file đề cương: <Mã>.<MSSV>.<Họ tên>.<Lớp>. Mỗi định
 * hướng có thể kèm một file PDF mô tả (tải lên, thay, gỡ) để SV/GV xem.
 */
export default function DinhHuongPage() {
  const { message } = AntApp.useApp()
  const { data, isLoading, isError, error, refetch } = useDinhHuong()
  const save = useSaveDinhHuong()
  const uploadTep = useUploadTepDinhHuong()
  const deleteTep = useDeleteTepDinhHuong()
  const [editing, setEditing] = useState<DinhHuongOut | 'new' | null>(null)
  const [form] = Form.useForm<DinhHuongInput>()

  const openForm = (item: DinhHuongOut | 'new') => {
    setEditing(item)
    form.setFieldsValue(
      item === 'new'
        ? { ma: '', ten: '', mo_ta: '', hoat_dong: true }
        : { ma: item.ma, ten: item.ten, mo_ta: item.mo_ta ?? '', hoat_dong: item.hoat_dong },
    )
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      await save.mutateAsync({
        id: editing === 'new' || editing === null ? undefined : editing.id,
        input: { ...values, ma: values.ma.trim().toUpperCase(), mo_ta: values.mo_ta || null },
      })
      message.success('Đã lưu định hướng')
      setEditing(null)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleUploadTep = (item: DinhHuongOut, file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      message.error(`"${file.name}" không phải file PDF.`)
      return false
    }
    if (file.size > MAX_TEP_BYTES) {
      message.error(`"${file.name}" vượt quá dung lượng tối đa 20 MB.`)
      return false
    }
    uploadTep
      .mutateAsync({ id: item.id, file })
      .then(() => message.success(`Đã tải lên file mô tả ${item.ma}`))
      .catch((err: unknown) => message.error(getErrorMessage(err)))
    // false: không tự upload theo cơ chế mặc định của antd — gửi qua axios ở trên.
    return false
  }

  const handleDeleteTep = async (item: DinhHuongOut) => {
    try {
      await deleteTep.mutateAsync(item.id)
      message.success(`Đã gỡ file mô tả ${item.ma}`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<DinhHuongOut> = [
    { title: 'STT', key: 'stt', width: 60, render: (_v, _r, index) => index + 1 },
    { title: 'Mã', dataIndex: 'ma', width: 90 },
    { title: 'Tên định hướng', dataIndex: 'ten' },
    { title: 'Mô tả', dataIndex: 'mo_ta', render: (v: string | null) => v || '—' },
    {
      title: 'File mô tả (PDF)',
      key: 'tep',
      width: 280,
      render: (_v, record) => (
        <div>
          {record.tep && (
            <div style={{ marginBottom: 6 }}>
              <div style={{ wordBreak: 'break-word' }}>{record.tep.ten_goc}</div>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {formatBytes(record.tep.kich_thuoc)} · cập nhật {formatDateTime(record.tep.cap_nhat_luc)}
              </Typography.Text>
            </div>
          )}
          <Space size={4} wrap>
            <TepMoTaButton dinhHuong={record} />
            <Upload
              accept=".pdf"
              maxCount={1}
              showUploadList={false}
              beforeUpload={(file) => handleUploadTep(record, file)}
            >
              <Button
                size="small"
                loading={uploadTep.isPending && uploadTep.variables?.id === record.id}
              >
                {record.tep ? 'Thay file' : 'Tải lên'}
              </Button>
            </Upload>
            {record.tep && (
              <Popconfirm
                title="Gỡ file mô tả của định hướng này?"
                description="Sinh viên và giảng viên sẽ không xem được file nữa."
                okText="Gỡ"
                cancelText="Hủy"
                okButtonProps={{ danger: true }}
                onConfirm={() => handleDeleteTep(record)}
              >
                <Button
                  size="small"
                  danger
                  loading={deleteTep.isPending && deleteTep.variables === record.id}
                >
                  Gỡ
                </Button>
              </Popconfirm>
            )}
          </Space>
        </div>
      ),
    },
    { title: 'Số đề tài', dataIndex: 'so_de_tai', width: 100 },
    {
      title: 'Trạng thái',
      dataIndex: 'hoat_dong',
      width: 130,
      render: (v: boolean) =>
        v ? <Tag color="success">Đang dùng</Tag> : <Tag>Ngừng sử dụng</Tag>,
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      width: 110,
      render: (_v, record) => (
        <Button size="small" onClick={() => openForm(record)}>
          Sửa
        </Button>
      ),
    },
  ]

  return (
    <Card
      title="Định hướng đề tài"
      extra={
        <Button type="primary" onClick={() => openForm('new')}>
          Thêm định hướng
        </Button>
      }
    >
      {isError ? (
        <QueryErrorAlert error={error} onRetry={() => void refetch()} />
      ) : (
        <Table<DinhHuongOut>
          rowKey="id"
          loading={isLoading}
          columns={columns}
          dataSource={data ?? []}
          pagination={false}
        />
      )}
      <Modal
        open={editing !== null}
        title={editing === 'new' ? 'Thêm định hướng' : 'Sửa định hướng'}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={save.isPending}
        onOk={() => void handleSave()}
        onCancel={() => setEditing(null)}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="ma"
            label="Mã định hướng"
            extra="Dạng H + 2 chữ số, ví dụ H01. Dùng làm phần đầu tên file đề cương."
            rules={[
              { required: true, message: 'Nhập mã định hướng' },
              { pattern: /^[Hh]\d{2}$/, message: 'Mã có dạng H01, H02, ...' },
            ]}
          >
            <Input maxLength={3} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item
            name="ten"
            label="Tên định hướng"
            rules={[{ required: true, min: 2, message: 'Nhập tên định hướng' }]}
          >
            <Input maxLength={255} />
          </Form.Item>
          <Form.Item name="mo_ta" label="Mô tả">
            <Input.TextArea rows={3} maxLength={2000} />
          </Form.Item>
          <Form.Item name="hoat_dong" label="Đang sử dụng" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
