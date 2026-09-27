import { useState } from 'react'
import {
  App as AntApp,
  Button,
  Checkbox,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Table,
  Tabs,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import {
  useAccounts,
  useCreateAccount,
  useSetAccountLocked,
  useUpdateAccount,
} from './api'
import type { AccountOut, VaiTroAccount } from './api'

const { Search } = Input

interface FormValues {
  ma: string
  email: string
  ho_ten: string
  lop?: string
  khoa?: string
  hoc_vi?: string
  mat_khau?: string
  dat_lai_mat_khau?: boolean
}

type TrangThaiFilter = 'all' | 'active' | 'locked'

export default function AccountsPage() {
  const { message } = AntApp.useApp()
  const [vaiTro, setVaiTro] = useState<VaiTroAccount>('SINH_VIEN')
  const [q, setQ] = useState('')
  const [trangThai, setTrangThai] = useState<TrangThaiFilter>('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<AccountOut | null>(null)
  const [form] = Form.useForm<FormValues>()
  const datLaiMatKhau = Form.useWatch('dat_lai_mat_khau', form)

  const { data, isFetching } = useAccounts({
    vai_tro: vaiTro,
    q: q || undefined,
    bi_khoa: trangThai === 'all' ? undefined : trangThai === 'locked',
    page,
    page_size: pageSize,
  })

  const createMutation = useCreateAccount()
  const updateMutation = useUpdateAccount()
  const lockMutation = useSetAccountLocked()

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: AccountOut) => {
    setEditing(record)
    form.setFieldsValue({
      ma: record.ma_dang_nhap,
      email: record.email,
      ho_ten: record.ho_ten,
      lop: record.lop ?? undefined,
      khoa: record.khoa ?? undefined,
      hoc_vi: record.hoc_vi ?? undefined,
      mat_khau: undefined,
      dat_lai_mat_khau: false,
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

    try {
      if (editing) {
        await updateMutation.mutateAsync({
          id: editing.tai_khoan_id,
          input: {
            email: values.email,
            ho_ten: values.ho_ten,
            lop: vaiTro === 'SINH_VIEN' ? values.lop : undefined,
            khoa: vaiTro === 'SINH_VIEN' ? values.khoa : undefined,
            hoc_vi: vaiTro === 'GIANG_VIEN' ? values.hoc_vi : undefined,
            mat_khau: values.dat_lai_mat_khau ? values.mat_khau : undefined,
          },
        })
        message.success('Đã cập nhật tài khoản')
      } else {
        await createMutation.mutateAsync({
          vai_tro: vaiTro,
          ma: values.ma,
          email: values.email,
          ho_ten: values.ho_ten,
          lop: vaiTro === 'SINH_VIEN' ? values.lop : undefined,
          khoa: vaiTro === 'SINH_VIEN' ? values.khoa : undefined,
          hoc_vi: vaiTro === 'GIANG_VIEN' ? values.hoc_vi : undefined,
          mat_khau: values.mat_khau ?? '',
        })
        message.success('Đã tạo tài khoản')
      }
      setModalOpen(false)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleToggleLock = async (record: AccountOut) => {
    try {
      await lockMutation.mutateAsync({ id: record.tai_khoan_id, locked: !record.bi_khoa })
      message.success(record.bi_khoa ? 'Đã mở khóa tài khoản' : 'Đã khóa tài khoản')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const middleColumn: ColumnsType<AccountOut>[number] =
    vaiTro === 'SINH_VIEN'
      ? { title: 'Lớp', dataIndex: 'lop' }
      : { title: 'Học vị', dataIndex: 'hoc_vi' }

  const columns: ColumnsType<AccountOut> = [
    { title: vaiTro === 'SINH_VIEN' ? 'Mã SV' : 'Mã GV', dataIndex: 'ma_dang_nhap' },
    { title: 'Họ tên', dataIndex: 'ho_ten' },
    middleColumn,
    { title: 'Email', dataIndex: 'email' },
    {
      title: 'Trạng thái',
      dataIndex: 'bi_khoa',
      render: (biKhoa: boolean) =>
        biKhoa ? <Tag color="red">Bị khóa</Tag> : <Tag color="green">Hoạt động</Tag>,
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
              record.bi_khoa
                ? 'Mở khóa tài khoản này?'
                : 'Khóa tài khoản này? Tài khoản bị khóa sẽ không thể đăng nhập cho tới khi được mở khóa.'
            }
            onConfirm={() => handleToggleLock(record)}
          >
            <Button size="small" danger={!record.bi_khoa}>
              {record.bi_khoa ? 'Mở khóa' : 'Khóa'}
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Quản lý tài khoản</h2>

      <Tabs
        activeKey={vaiTro}
        onChange={(key) => {
          setVaiTro(key as VaiTroAccount)
          setPage(1)
        }}
        items={[
          { key: 'SINH_VIEN', label: 'Sinh viên' },
          { key: 'GIANG_VIEN', label: 'Giảng viên' },
        ]}
      />

      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <Search
          placeholder="Tìm theo mã, họ tên hoặc email"
          allowClear
          style={{ width: 280 }}
          onSearch={(value) => {
            setQ(value)
            setPage(1)
          }}
        />
        <Select<TrangThaiFilter>
          style={{ width: 160 }}
          value={trangThai}
          onChange={(value) => {
            setTrangThai(value)
            setPage(1)
          }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'active', label: 'Hoạt động' },
            { value: 'locked', label: 'Bị khóa' },
          ]}
        />
        <Button type="primary" onClick={openCreate} style={{ marginLeft: 'auto' }}>
          Thêm tài khoản
        </Button>
      </div>

      <Table<AccountOut>
        rowKey="tai_khoan_id"
        loading={isFetching}
        columns={columns}
        dataSource={data?.items ?? []}
        pagination={{
          current: page,
          pageSize,
          total: data?.total ?? 0,
          showSizeChanger: true,
          onChange: (nextPage, nextPageSize) => {
            setPage(nextPage)
            setPageSize(nextPageSize)
          },
        }}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa tài khoản' : 'Thêm tài khoản'}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label={vaiTro === 'SINH_VIEN' ? 'Mã SV' : 'Mã GV'}
            name="ma"
            rules={[{ required: true, message: 'Vui lòng nhập mã' }]}
          >
            <Input disabled={!!editing} />
          </Form.Item>
          <Form.Item
            label="Họ tên"
            name="ho_ten"
            rules={[{ required: true, message: 'Vui lòng nhập họ tên' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Email"
            name="email"
            rules={[{ required: true, message: 'Vui lòng nhập email' }]}
          >
            <Input />
          </Form.Item>

          {vaiTro === 'SINH_VIEN' ? (
            <>
              <Form.Item label="Lớp" name="lop">
                <Input />
              </Form.Item>
              <Form.Item label="Khoa" name="khoa">
                <Input />
              </Form.Item>
            </>
          ) : (
            <Form.Item label="Học vị" name="hoc_vi">
              <Input />
            </Form.Item>
          )}

          {editing ? (
            <>
              <Form.Item name="dat_lai_mat_khau" valuePropName="checked">
                <Checkbox>Đặt lại mật khẩu</Checkbox>
              </Form.Item>
              {datLaiMatKhau && (
                <Form.Item
                  label="Mật khẩu mới"
                  name="mat_khau"
                  rules={[{ required: true, min: 8, message: 'Mật khẩu tối thiểu 8 ký tự' }]}
                >
                  <Input.Password />
                </Form.Item>
              )}
            </>
          ) : (
            <Form.Item
              label="Mật khẩu"
              name="mat_khau"
              rules={[{ required: true, min: 8, message: 'Mật khẩu tối thiểu 8 ký tự' }]}
            >
              <Input.Password />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}
