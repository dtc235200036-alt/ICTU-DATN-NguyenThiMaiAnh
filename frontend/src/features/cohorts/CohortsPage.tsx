import { useState } from 'react'
import { App as AntApp, Button, Form, Input, Modal, Popconfirm, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import { useCohorts, useCreateCohort, useSetCohortState, useUpdateCohort } from './api'
import type { CohortFormInput, CohortOut } from './api'

interface FormValues {
  ten_dot: string
  khoa: string
  nam_hoc?: string
  ngay_bat_dau: string
  ngay_ket_thuc?: string
}

function toDisplayDate(value: string | null): string {
  if (!value) return '—'
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

export default function CohortsPage() {
  const { message } = AntApp.useApp()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<CohortOut | null>(null)
  const [form] = Form.useForm<FormValues>()

  const { data, isFetching } = useCohorts()
  const createMutation = useCreateCohort()
  const updateMutation = useUpdateCohort()
  const stateMutation = useSetCohortState()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: CohortOut) => {
    setEditing(record)
    form.setFieldsValue({
      ten_dot: record.ten_dot,
      khoa: record.khoa,
      nam_hoc: record.nam_hoc ?? undefined,
      ngay_bat_dau: record.ngay_bat_dau,
      ngay_ket_thuc: record.ngay_ket_thuc ?? undefined,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    let values: FormValues
    try {
      values = await form.validateFields()
    } catch {
      return // Lỗi hiển thị ngay tại từng Form.Item, không cần message riêng.
    }

    const input: CohortFormInput = {
      ten_dot: values.ten_dot,
      khoa: values.khoa,
      nam_hoc: values.nam_hoc || null,
      ngay_bat_dau: values.ngay_bat_dau,
      ngay_ket_thuc: values.ngay_ket_thuc || null,
    }

    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, input })
        message.success('Đã cập nhật đợt đồ án')
      } else {
        await createMutation.mutateAsync(input)
        message.success('Đã mở đợt đồ án mới')
      }
      setModalOpen(false)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleToggleState = async (record: CohortOut) => {
    try {
      await stateMutation.mutateAsync({
        id: record.id,
        action: record.trang_thai === 'DANG_MO' ? 'close' : 'open',
      })
      message.success(record.trang_thai === 'DANG_MO' ? 'Đã đóng đợt' : 'Đã mở lại đợt')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<CohortOut> = [
    { title: 'Tên đợt', dataIndex: 'ten_dot' },
    { title: 'Khóa', dataIndex: 'khoa' },
    { title: 'Năm học', dataIndex: 'nam_hoc', render: (v: string | null) => v ?? '—' },
    { title: 'Ngày bắt đầu', dataIndex: 'ngay_bat_dau', render: toDisplayDate },
    { title: 'Ngày kết thúc', dataIndex: 'ngay_ket_thuc', render: toDisplayDate },
    {
      title: 'Trạng thái',
      dataIndex: 'trang_thai',
      render: (trangThai: CohortOut['trang_thai']) =>
        trangThai === 'DANG_MO' ? (
          <Tag color="processing">Đang mở</Tag>
        ) : (
          <Tag>Đã đóng</Tag>
        ),
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button size="small" onClick={() => openEdit(record)}>
            Sửa
          </Button>
          <Popconfirm
            title={
              record.trang_thai === 'DANG_MO'
                ? 'Đóng đợt đồ án này? Đóng đợt sẽ chặn giao đề tài mới cho tới khi mở lại.'
                : 'Mở lại đợt đồ án này?'
            }
            onConfirm={() => handleToggleState(record)}
          >
            <Button size="small" danger={record.trang_thai === 'DANG_MO'}>
              {record.trang_thai === 'DANG_MO' ? 'Đóng đợt' : 'Mở lại'}
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Quản lý đợt đồ án</h2>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <Button type="primary" onClick={openCreate}>
          Mở đợt mới
        </Button>
      </div>

      <Table<CohortOut>
        rowKey="id"
        loading={isFetching}
        columns={columns}
        dataSource={data ?? []}
        pagination={false}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa đợt đồ án' : 'Mở đợt mới'}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="Tên đợt"
            name="ten_dot"
            rules={[{ required: true, message: 'Vui lòng nhập tên đợt' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Khóa"
            name="khoa"
            rules={[
              { required: true, message: 'Vui lòng nhập khóa' },
              { pattern: /^K\d{2}$/, message: 'Khóa phải theo dạng K + 2 chữ số, ví dụ K23' },
            ]}
          >
            <Input placeholder="K23" />
          </Form.Item>
          <Form.Item
            label="Năm học"
            name="nam_hoc"
            rules={[{ pattern: /^\d{4}-\d{4}$/, message: 'Năm học phải theo dạng YYYY-YYYY' }]}
          >
            <Input placeholder="2026-2027" />
          </Form.Item>
          <Form.Item
            label="Ngày bắt đầu"
            name="ngay_bat_dau"
            rules={[{ required: true, message: 'Vui lòng chọn ngày bắt đầu' }]}
          >
            <Input type="date" />
          </Form.Item>
          <Form.Item label="Ngày kết thúc" name="ngay_ket_thuc">
            <Input type="date" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
