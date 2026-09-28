import { useEffect } from 'react'
import { App as AntApp, Form, Input, InputNumber, Modal, Select } from 'antd'

import { getErrorMessage } from '../../api/client'
import { useLecturers } from '../accounts/api'
import { useCreateArchive, useUpdateArchive } from './api'
import type { ArchiveDetail, ArchiveIn } from './api'

interface FormValues {
  khoa: string
  ten_de_tai: string
  ma_so_sinh_vien?: string
  ho_ten_sinh_vien?: string
  giang_vien_id?: number | null
  tu_khoa?: string
  diem?: number | null
}

export interface ArchiveFormModalProps {
  open: boolean
  /** undefined = thêm mới; có giá trị = sửa bản ghi đó. */
  record?: ArchiveDetail
  onClose: () => void
  onSaved?: (saved: ArchiveDetail) => void
}

/**
 * UC5.3 (MH-13): Bộ môn thêm/sửa metadata một bản ghi kho. Giới hạn độ dài
 * khớp schemas/archive.py; 409 (trùng khóa + tên đề tài) / 422 hiển thị
 * nguyên thông điệp của server.
 */
export default function ArchiveFormModal({ open, record, onClose, onSaved }: ArchiveFormModalProps) {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm<FormValues>()
  const { data: lecturers } = useLecturers()
  const createMutation = useCreateArchive()
  const updateMutation = useUpdateArchive()
  const isEdit = record !== undefined
  // WR-09: bản ghi tự lưu khi chốt bảo vệ — điểm và danh tính SV chỉ đọc.
  const lockedDefense = record?.nguon === 'HE_THONG'

  useEffect(() => {
    if (!open) return
    if (record) {
      form.setFieldsValue({
        khoa: record.khoa ?? '',
        ten_de_tai: record.ten_de_tai,
        ma_so_sinh_vien: record.sinh_vien?.ma ?? undefined,
        ho_ten_sinh_vien: record.sinh_vien?.ho_ten ?? undefined,
        giang_vien_id: record.giang_vien?.id ?? null,
        tu_khoa: record.tu_khoa ?? undefined,
        diem: record.diem,
      })
    } else {
      form.resetFields()
    }
  }, [open, record, form])

  const handleOk = async () => {
    const values = await form.validateFields()
    const payload: ArchiveIn = {
      khoa: values.khoa,
      ten_de_tai: values.ten_de_tai,
      ma_so_sinh_vien: values.ma_so_sinh_vien || null,
      ho_ten_sinh_vien: values.ho_ten_sinh_vien || null,
      giang_vien_id: values.giang_vien_id ?? null,
      tu_khoa: values.tu_khoa || null,
      diem: values.diem ?? null,
    }
    try {
      const saved = record
        ? await updateMutation.mutateAsync({ id: record.id, payload })
        : await createMutation.mutateAsync(payload)
      message.success(record ? 'Đã cập nhật bản ghi kho' : 'Đã thêm bản ghi kho')
      onSaved?.(saved)
      onClose()
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  return (
    <Modal
      open={open}
      title={isEdit ? 'Sửa bản ghi kho' : 'Thêm bản ghi kho'}
      okText={isEdit ? 'Lưu' : 'Thêm'}
      cancelText="Hủy"
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      destroyOnClose
    >
      <Form<FormValues> form={form} layout="vertical" preserve={false}>
        <Form.Item
          name="khoa"
          label="Khóa"
          rules={[
            { required: true, whitespace: true, message: 'Vui lòng nhập khóa' },
            { max: 20, message: 'Khóa tối đa 20 ký tự' },
          ]}
        >
          <Input placeholder="Ví dụ: K19" />
        </Form.Item>
        <Form.Item
          name="ten_de_tai"
          label="Tên đề tài"
          rules={[
            { required: true, whitespace: true, message: 'Vui lòng nhập tên đề tài' },
            { max: 255, message: 'Tên đề tài tối đa 255 ký tự' },
          ]}
        >
          <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
        </Form.Item>
        <div style={{ display: 'flex', gap: 12 }}>
          <Form.Item
            name="ma_so_sinh_vien"
            label="Mã SV"
            style={{ flex: 1 }}
            rules={[{ max: 20, message: 'Mã SV tối đa 20 ký tự' }]}
          >
            <Input disabled={lockedDefense} />
          </Form.Item>
          <Form.Item
            name="ho_ten_sinh_vien"
            label="Họ tên SV"
            style={{ flex: 2 }}
            rules={[{ max: 150, message: 'Họ tên tối đa 150 ký tự' }]}
          >
            <Input disabled={lockedDefense} />
          </Form.Item>
        </div>
        <Form.Item name="giang_vien_id" label="GVHD">
          <Select
            allowClear
            showSearch
            placeholder="Chọn giảng viên hướng dẫn"
            filterOption={(input, option) =>
              (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
            }
            options={(lecturers ?? []).map((gv) => ({
              value: gv.id,
              label: `${gv.hoc_vi ?? ''} ${gv.ho_ten ?? ''}`.trim(),
            }))}
          />
        </Form.Item>
        <Form.Item
          name="tu_khoa"
          label="Từ khóa"
          extra="Phân tách bằng dấu phẩy"
          rules={[{ max: 255, message: 'Từ khóa tối đa 255 ký tự' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="diem"
          label="Điểm"
          extra={lockedDefense ? 'Điểm chính thức từ kết quả chốt bảo vệ — không sửa được' : undefined}
        >
          <InputNumber
            min={0}
            max={10}
            step={0.1}
            precision={2}
            style={{ width: 160 }}
            disabled={lockedDefense}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}
