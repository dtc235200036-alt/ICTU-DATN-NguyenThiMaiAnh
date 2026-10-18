import { useState } from 'react'
import { App as AntApp, Button, Card, Form, Input, Modal, Switch, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import { useDinhHuong, useSaveDinhHuong } from './api'
import type { DinhHuongInput, DinhHuongOut } from './api'

/**
 * Bộ môn quản lý danh mục định hướng đề tài (thay cho "Lĩnh vực"). Mã định
 * hướng là phần đầu tên file đề cương: <Mã>.<MSSV>.<Họ tên>.<Lớp>.
 */
export default function DinhHuongPage() {
  const { message } = AntApp.useApp()
  const { data, isLoading, isError, error, refetch } = useDinhHuong()
  const save = useSaveDinhHuong()
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

  const columns: ColumnsType<DinhHuongOut> = [
    { title: 'STT', key: 'stt', width: 60, render: (_v, _r, index) => index + 1 },
    { title: 'Mã', dataIndex: 'ma', width: 90 },
    { title: 'Tên định hướng', dataIndex: 'ten' },
    { title: 'Mô tả', dataIndex: 'mo_ta', render: (v: string | null) => v || '—' },
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
