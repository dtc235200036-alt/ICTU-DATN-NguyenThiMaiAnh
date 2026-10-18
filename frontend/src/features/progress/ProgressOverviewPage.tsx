import { useState } from 'react'
import {
  App as AntApp,
  Button,
  Card,
  Checkbox,
  Col,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useCohorts } from '../cohorts/api'
import { trangThaiDeCuong } from '../outlines/constants'
import { useDeleteMilestone, useMilestones, useProgressDashboard, useSaveMilestone } from './api'
import type { LocDeCuong, MilestoneOut, ProgressRow } from './api'
import { TRANG_THAI_MOC, formatDay } from './constants'

const { Text } = Typography
const PAGE_SIZE = 20

interface MilestoneFormValues {
  ten_moc: string
  han_nop: string
}

/**
 * MH-04 "Tiến độ toàn khoa" (UC3.1 + UC3.4): Bộ môn chọn đợt, thiết lập mốc
 * (tên + hạn nộp) và xem ma trận SV × mốc với trạng thái do server tính từ
 * ngày (D-05); "Chỉ SV trễ mốc" lọc SV có mốc trễ (UC3.4 A1). Đợt, bộ lọc và
 * trang nằm trên URL.
 */
export default function ProgressOverviewPage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const dotParam = searchParams.get('dot_do_an_id')
  const chiTreMoc = searchParams.get('chi_tre_moc') === '1'
  const page = Number(searchParams.get('page') ?? '1') || 1
  const q = searchParams.get('q') ?? undefined
  const locDeCuong = (searchParams.get('loc_de_cuong') as LocDeCuong | null) ?? undefined

  const { data: cohorts } = useCohorts()
  const { data: dashboard, isFetching } = useProgressDashboard({
    dot_do_an_id: dotParam ? Number(dotParam) : undefined,
    chi_tre_moc: chiTreMoc,
    q,
    loc_de_cuong: locDeCuong,
    page,
    page_size: PAGE_SIZE,
  })
  const dotId = dotParam ? Number(dotParam) : dashboard?.dot_do_an?.id
  const { data: milestones, isFetching: milestonesFetching } = useMilestones(dotId)
  const saveMutation = useSaveMilestone()
  const deleteMutation = useDeleteMilestone()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<MilestoneOut | null>(null)
  const [form] = Form.useForm<MilestoneFormValues>()

  const cohortClosed = dashboard?.dot_do_an?.trang_thai === 'DA_DONG'

  const updateParams = (changes: Record<string, string | undefined>) => {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(changes)) {
      if (value === undefined) next.delete(key)
      else next.set(key, value)
    }
    setSearchParams(next, { replace: true })
  }

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (m: MilestoneOut) => {
    setEditing(m)
    form.setFieldsValue({ ten_moc: m.ten_moc, han_nop: m.han_nop ?? '' })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (dotId === undefined) return
    const values = await form.validateFields()
    try {
      await saveMutation.mutateAsync({
        id: editing?.id,
        dot_do_an_id: dotId,
        ten_moc: values.ten_moc.trim(),
        han_nop: values.han_nop,
      })
      message.success(editing ? 'Đã cập nhật mốc tiến độ' : 'Đã thêm mốc tiến độ')
      setModalOpen(false)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleDelete = async (m: MilestoneOut) => {
    try {
      await deleteMutation.mutateAsync(m.id)
      message.success(`Đã xóa ${m.ten_moc}`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const milestoneColumns: ColumnsType<MilestoneOut> = [
    { title: 'Mốc', dataIndex: 'ten_moc', key: 'ten_moc' },
    {
      title: 'Hạn nộp',
      dataIndex: 'han_nop',
      key: 'han_nop',
      render: (value: string | null) => formatDay(value),
    },
    {
      title: 'Hành động',
      key: 'actions',
      render: (_v, record) => (
        <Space size={4}>
          <Button type="link" size="small" disabled={cohortClosed} onClick={() => openEdit(record)}>
            Sửa
          </Button>
          <Popconfirm
            title={`Xóa ${record.ten_moc}?`}
            description={
              record.so_bao_cao > 0
                ? `Mốc đã có ${record.so_bao_cao} báo cáo — hệ thống sẽ từ chối, hãy sửa hạn nộp.`
                : 'Mốc chưa có báo cáo nào.'
            }
            okText="Xóa"
            cancelText="Hủy"
            onConfirm={() => handleDelete(record)}
            disabled={cohortClosed}
          >
            <Button type="link" size="small" danger disabled={cohortClosed}>
              Xóa
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const moc = dashboard?.moc ?? []
  const progressColumns: ColumnsType<ProgressRow> = [
    {
      title: 'STT',
      key: 'stt',
      width: 60,
      render: (_v, _r, index) => (page - 1) * PAGE_SIZE + index + 1,
    },
    {
      title: 'Sinh viên',
      key: 'sinh_vien',
      render: (_v, r) =>
        r.sinh_vien ? `${r.sinh_vien.ho_ten}${r.sinh_vien.ma ? ` (${r.sinh_vien.ma})` : ''}` : '—',
    },
    { title: 'Đề tài', key: 'de_tai', render: (_v, r) => r.de_tai.ten_de_tai },
    {
      title: 'GVHD',
      key: 'giang_vien',
      render: (_v, r) => r.giang_vien?.ho_ten ?? '—',
    },
    {
      title: 'Đề cương',
      key: 'de_cuong',
      render: (_v, r) => {
        const info = trangThaiDeCuong(r.trang_thai_de_cuong)
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    ...moc.map((m) => ({
      title: m.ten_moc,
      key: `moc-${m.id}`,
      render: (_v: unknown, r: ProgressRow) => {
        const cell = r.o.find((c) => c.moc_id === m.id)
        if (!cell) return '—'
        const s = TRANG_THAI_MOC[cell.trang_thai]
        return <Tag color={s.color}>{s.label}</Tag>
      },
    })),
  ]

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={10}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
              Đợt đồ án
            </Text>
            <Select
              style={{ width: '100%' }}
              value={dotId}
              placeholder="Chọn đợt đồ án"
              onChange={(value: number) =>
                updateParams({ dot_do_an_id: String(value), page: undefined })
              }
              options={(cohorts ?? []).map((c) => ({
                value: c.id,
                label: `${c.ten_dot} (${c.khoa})${c.trang_thai === 'DA_DONG' ? ' · đã đóng' : ''}`,
              }))}
            />
          </Col>
          <Col xs={12} md={3}>
            <Statistic title="Tổng SV" value={dashboard?.tong_sv ?? 0} />
          </Col>
          <Col xs={12} md={4}>
            <Statistic title="Đã nộp đề cương" value={dashboard?.da_nop_de_cuong ?? 0} />
          </Col>
          <Col xs={12} md={4}>
            <Statistic title="Chưa hoàn thành" value={dashboard?.chua_hoan_thanh ?? 0} />
          </Col>
          <Col xs={12} md={3}>
            <Statistic
              title="SV trễ mốc"
              value={dashboard?.so_sv_tre_moc ?? 0}
              valueStyle={{ color: (dashboard?.so_sv_tre_moc ?? 0) > 0 ? '#cf1322' : undefined }}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={16}>
          <Card
            title="Tiến độ toàn khoa"
            extra={
              <Checkbox
                checked={chiTreMoc}
                onChange={(e) =>
                  updateParams({ chi_tre_moc: e.target.checked ? '1' : undefined, page: undefined })
                }
              >
                Chỉ SV trễ mốc
              </Checkbox>
            }
          >
            <Input.Search
              allowClear
              defaultValue={q}
              placeholder="Tìm tên SV, mã SV, đề tài, GVHD..."
              style={{ maxWidth: 420, marginBottom: 8 }}
              onSearch={(value) => updateParams({ q: value.trim() || undefined, page: undefined })}
            />
            <Tabs
              activeKey={locDeCuong ?? 'TAT_CA'}
              onChange={(key) =>
                updateParams({ loc_de_cuong: key === 'TAT_CA' ? undefined : key, page: undefined })
              }
              items={[
                { key: 'TAT_CA', label: 'Tất cả' },
                { key: 'DA_NOP', label: 'Đã nộp đề cương' },
                { key: 'CHO_DUYET', label: 'Chờ duyệt' },
                { key: 'CHUA_NOP', label: 'Chưa nộp' },
              ]}
            />
            <Table<ProgressRow>
              rowKey={(r) => r.de_tai.id}
              columns={progressColumns}
              dataSource={dashboard?.items ?? []}
              loading={isFetching}
              scroll={{ x: true }}
              locale={{
                emptyText: chiTreMoc ? 'Không có SV trễ mốc' : 'Chưa có SV được phân công trong đợt',
              }}
              pagination={{
                current: page,
                pageSize: PAGE_SIZE,
                total: dashboard?.total ?? 0,
                showSizeChanger: false,
                onChange: (p) => updateParams({ page: p > 1 ? String(p) : undefined }),
              }}
            />
          </Card>
        </Col>
        <Col xs={24} xl={8}>
          <Card title="Mốc tiến độ của đợt">
            <Table<MilestoneOut>
              rowKey="id"
              size="small"
              columns={milestoneColumns}
              dataSource={milestones ?? []}
              loading={milestonesFetching}
              pagination={false}
              locale={{ emptyText: 'Chưa có mốc tiến độ' }}
            />
            <Button
              type="primary"
              block
              style={{ marginTop: 16 }}
              disabled={dotId === undefined || cohortClosed}
              onClick={openCreate}
            >
              Thiết lập mốc
            </Button>
          </Card>
        </Col>
      </Row>

      <Modal
        title={editing ? `Sửa ${editing.ten_moc}` : 'Thiết lập mốc'}
        open={modalOpen}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={saveMutation.isPending}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="ten_moc"
            label="Tên mốc"
            rules={[
              { required: true, whitespace: true, message: 'Vui lòng nhập tên mốc' },
              { max: 100, message: 'Tối đa 100 ký tự' },
            ]}
          >
            <Input placeholder="Mốc 1, Mốc 2, Mốc cuối..." />
          </Form.Item>
          <Form.Item
            name="han_nop"
            label="Hạn nộp"
            rules={[{ required: true, message: 'Vui lòng chọn hạn nộp' }]}
          >
            <Input type="date" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}
