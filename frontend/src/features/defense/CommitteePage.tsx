import { useEffect, useState } from 'react'
import {
  App as AntApp,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  List,
  Popconfirm,
  Row,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Tooltip,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { formatDate } from '../../utils/format'
import { useLecturers } from '../accounts/api'
import CheckStatusTag from '../documents/CheckStatusTag'
import {
  useAddSchedule,
  useCommittee,
  useCommittees,
  useDeleteCommittee,
  useEligibleStudents,
  useFinalize,
  useRemoveSchedule,
  useSaveCommittee,
} from './api'
import type { CommitteeIn, CommitteeListItem, ScheduleRow, VaiTroThanhVien } from './api'

const VAI_TRO_OPTIONS: { value: VaiTroThanhVien; label: string }[] = [
  { value: 'CHU_TICH', label: 'Chủ tịch' },
  { value: 'THU_KY', label: 'Thư ký' },
  { value: 'UY_VIEN', label: 'Ủy viên' },
]

const MIN_MEMBERS = 3
const MAX_MEMBERS = 5

interface MemberFormValue {
  giang_vien_id?: number
  vai_tro?: VaiTroThanhVien
}

interface CommitteeFormValues {
  ten_hoi_dong: string
  ngay_bao_ve: string
  gio_bao_ve: string
  phong: string
  thanh_vien: MemberFormValue[]
}

function renderPerson(person: { ho_ten: string; ma?: string | null } | null): string {
  if (!person) return '—'
  return person.ma ? `${person.ho_ten} (${person.ma})` : person.ho_ten
}

/**
 * MH-11/UC4.2: Bộ môn lập hội đồng (tên/ngày/giờ/phòng + 3-5 thành viên,
 * đúng 1 Chủ tịch) và xếp lịch SV đủ điều kiện bảo vệ vào hội đồng — server
 * chặn 409 khi GVHD của SV là thành viên hội đồng (D-06); UI vô hiệu hóa lựa
 * chọn đó trước để tránh round-trip vô ích. UC4.4 (plan 03-04): "Chốt kết
 * quả" chỉ bật khi đủ mọi thành viên đã chấm; server vẫn tự kiểm tra (409).
 */
export default function CommitteePage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawId = searchParams.get('hoi_dong_id')
  const isNew = rawId === 'moi'
  const selectedId = !isNew && rawId ? Number(rawId) : undefined

  const { data: committees, isFetching: isListFetching } = useCommittees()
  const { data: committee, isFetching: isDetailFetching } = useCommittee(selectedId)
  const { data: lecturers } = useLecturers()
  const { data: eligibleStudents } = useEligibleStudents()

  const [form] = Form.useForm<CommitteeFormValues>()
  const saveMutation = useSaveCommittee()
  const deleteMutation = useDeleteCommittee()
  const addScheduleMutation = useAddSchedule()
  const removeScheduleMutation = useRemoveSchedule()
  const finalizeMutation = useFinalize()
  const [selectedStudent, setSelectedStudent] = useState<number | undefined>(undefined)

  useEffect(() => {
    if (isNew) {
      form.resetFields()
      form.setFieldsValue({ thanh_vien: [{}, {}, {}] })
    } else if (committee) {
      form.setFieldsValue({
        ten_hoi_dong: committee.ten_hoi_dong,
        ngay_bao_ve: committee.ngay_bao_ve,
        gio_bao_ve: committee.gio_bao_ve.slice(0, 5),
        phong: committee.phong,
        thanh_vien: committee.thanh_vien.map((m) => ({
          giang_vien_id: m.giang_vien.id,
          vai_tro: m.vai_tro,
        })),
      })
    }
    setSelectedStudent(undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isNew, committee?.id])

  const selectCommittee = (id: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('hoi_dong_id', String(id))
    setSearchParams(next, { replace: true })
  }

  const startNew = () => {
    const next = new URLSearchParams(searchParams)
    next.set('hoi_dong_id', 'moi')
    setSearchParams(next, { replace: true })
  }

  const handleSave = async () => {
    let values: CommitteeFormValues
    try {
      values = await form.validateFields()
    } catch {
      return // lỗi đã hiển thị ngay tại từng Form.Item
    }

    const input: CommitteeIn = {
      ten_hoi_dong: values.ten_hoi_dong,
      ngay_bao_ve: values.ngay_bao_ve,
      gio_bao_ve: values.gio_bao_ve,
      phong: values.phong,
      thanh_vien: values.thanh_vien.map((m) => ({
        giang_vien_id: m.giang_vien_id as number,
        vai_tro: m.vai_tro as VaiTroThanhVien,
      })),
    }

    try {
      const saved = await saveMutation.mutateAsync({ id: isNew ? undefined : selectedId, input })
      message.success(isNew ? 'Đã tạo hội đồng' : 'Đã lưu hội đồng và lịch')
      if (isNew) {
        const next = new URLSearchParams(searchParams)
        next.set('hoi_dong_id', String(saved.id))
        setSearchParams(next, { replace: true })
      }
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleDelete = async () => {
    if (selectedId === undefined) return
    try {
      await deleteMutation.mutateAsync(selectedId)
      message.success('Đã xóa hội đồng')
      const next = new URLSearchParams(searchParams)
      next.delete('hoi_dong_id')
      setSearchParams(next, { replace: true })
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleAddStudent = async () => {
    if (committee === undefined || selectedStudent === undefined) return
    try {
      await addScheduleMutation.mutateAsync({ hoiDongId: committee.id, deTaiId: selectedStudent })
      message.success('Đã thêm sinh viên vào lịch bảo vệ')
      setSelectedStudent(undefined)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleFinalize = async (lichBaoVeId: number) => {
    if (committee === undefined) return
    try {
      const { data } = await finalizeMutation.mutateAsync({ hoiDongId: committee.id, lichId: lichBaoVeId })
      const diem = data.lich.diem_trung_binh
      message.success(`Đã chốt kết quả${diem !== null ? ` — điểm ${diem.toFixed(2)}` : ''}; đồ án đã vào kho`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleRemoveStudent = async (lichBaoVeId: number) => {
    if (committee === undefined) return
    try {
      await removeScheduleMutation.mutateAsync({ hoiDongId: committee.id, lichBaoVeId })
      message.success('Đã gỡ sinh viên khỏi lịch bảo vệ')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const memberGvIds = new Set((committee?.thanh_vien ?? []).map((m) => m.giang_vien.id))
  const hasScores = (committee?.lich ?? []).some((row) => row.so_da_cham > 0)
  const canDelete = committee !== undefined && committee.lich.length === 0

  const lecturerOptions = (lecturers ?? []).map((gv) => ({
    value: gv.id,
    label: [gv.hoc_vi, gv.ho_ten].filter(Boolean).join(' ') || `GV #${gv.id}`,
  }))

  const studentOptions = (eligibleStudents ?? []).map((item) => {
    const conflicts = item.giang_vien_id !== null && memberGvIds.has(item.giang_vien_id)
    return {
      value: item.de_tai_id,
      disabled: conflicts,
      label: `${renderPerson(item.sinh_vien)} — ${item.ten_de_tai}${
        conflicts ? ' (GVHD là thành viên hội đồng)' : ''
      }`,
    }
  })

  const scheduleColumns: ColumnsType<ScheduleRow> = [
    { title: 'TT', dataIndex: 'thu_tu', width: 50, render: (v: number | null) => v ?? '—' },
    {
      title: 'Sinh viên / Đề tài',
      key: 'sv_de_tai',
      render: (_value, record) => (
        <div>
          <div>{renderPerson(record.sinh_vien)}</div>
          <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>{record.ten_de_tai}</div>
        </div>
      ),
    },
    { title: 'Giờ', dataIndex: 'gio_du_kien' },
    {
      title: 'Chấm điểm',
      key: 'cham_diem',
      render: (_value, record) => (
        <Tag color={record.so_da_cham === record.so_thanh_vien ? 'success' : 'warning'}>
          {record.so_da_cham}/{record.so_thanh_vien} đã chấm
        </Tag>
      ),
    },
    {
      title: 'Điểm TB',
      key: 'diem_tb',
      render: (_value, record) => {
        const value = record.da_chot ? record.diem_trung_binh : record.diem_tam_tinh
        return value !== null && value !== undefined ? value.toFixed(2) : '—'
      },
    },
    {
      title: 'Kiểm tra trùng lặp',
      key: 'kiem_tra',
      render: (_value, record) => <CheckStatusTag kiemTra={record.kiem_tra} />,
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => {
        if (record.da_chot) {
          return <Tag color="success">Đã chốt</Tag>
        }
        const waiting = <span style={{ color: 'rgba(0,0,0,0.45)' }}>Chờ tất cả thành viên chấm</span>
        if (record.so_da_cham === 0) {
          return (
            <Space direction="vertical" size={4}>
              <Popconfirm
                title="Gỡ sinh viên này khỏi lịch bảo vệ?"
                onConfirm={() => void handleRemoveStudent(record.id)}
              >
                <Button size="small" danger loading={removeScheduleMutation.isPending}>
                  Gỡ khỏi lịch
                </Button>
              </Popconfirm>
              {waiting}
            </Space>
          )
        }
        if (record.so_da_cham < record.so_thanh_vien) {
          return waiting
        }
        const tamTinh = record.diem_tam_tinh !== null ? record.diem_tam_tinh.toFixed(2) : '—'
        return (
          <Popconfirm
            title="Chốt kết quả bảo vệ?"
            description={`Điểm = trung bình cộng ${record.so_thanh_vien} thành viên (${tamTinh}). Sau khi chốt không thể sửa điểm; đồ án được đưa vào kho.`}
            onConfirm={() => void handleFinalize(record.id)}
          >
            <Button size="small" type="primary" loading={finalizeMutation.isPending}>
              Chốt kết quả
            </Button>
          </Popconfirm>
        )
      },
    },
  ]

  return (
    <Row gutter={20}>
      <Col xs={24} lg={7}>
        <Card
          title="Danh sách hội đồng"
          extra={
            <Button size="small" type="primary" onClick={startNew}>
              Tạo hội đồng
            </Button>
          }
        >
          <List<CommitteeListItem>
            loading={isListFetching}
            dataSource={committees ?? []}
            locale={{ emptyText: 'Chưa có hội đồng nào' }}
            renderItem={(item) => (
              <List.Item
                onClick={() => selectCommittee(item.id)}
                style={{
                  cursor: 'pointer',
                  background: selectedId === item.id ? 'rgba(22,119,255,0.06)' : undefined,
                  padding: '8px 12px',
                }}
              >
                <div style={{ width: '100%' }}>
                  <div>
                    {item.ten_hoi_dong} — {formatDate(item.ngay_bao_ve)} {item.gio_bao_ve.slice(0, 5)}{' '}
                    — Phòng {item.phong}
                  </div>
                  <Tag style={{ marginTop: 4 }}>{item.so_sinh_vien} SV</Tag>
                </div>
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col xs={24} lg={17}>
        {!isNew && selectedId === undefined ? (
          <Card>
            <Empty description="Chọn một hội đồng ở danh sách bên trái, hoặc tạo hội đồng mới" />
          </Card>
        ) : isDetailFetching && !isNew ? (
          <Card>
            <Skeleton active />
          </Card>
        ) : (
          <>
            <Card title="Thông tin hội đồng" style={{ marginBottom: 20 }}>
              <Form form={form} layout="vertical" initialValues={{ thanh_vien: [{}, {}, {}] }}>
                <Row gutter={12}>
                  <Col xs={24} md={10}>
                    <Form.Item
                      label="Tên hội đồng"
                      name="ten_hoi_dong"
                      rules={[{ required: true, message: 'Vui lòng nhập tên hội đồng' }]}
                    >
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col xs={12} md={5}>
                    <Form.Item
                      label="Ngày"
                      name="ngay_bao_ve"
                      rules={[{ required: true, message: 'Chọn ngày' }]}
                    >
                      <Input type="date" disabled={hasScores} />
                    </Form.Item>
                  </Col>
                  <Col xs={12} md={5}>
                    <Form.Item
                      label="Giờ"
                      name="gio_bao_ve"
                      rules={[{ required: true, message: 'Chọn giờ' }]}
                    >
                      <Input type="time" disabled={hasScores} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={4}>
                    <Form.Item
                      label="Phòng"
                      name="phong"
                      rules={[{ required: true, message: 'Nhập phòng' }]}
                    >
                      <Input disabled={hasScores} />
                    </Form.Item>
                  </Col>
                </Row>

                <h3 style={{ fontSize: 14, fontWeight: 600, margin: '8px 0' }}>
                  Thành viên hội đồng
                </h3>
                <Form.List name="thanh_vien">
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map((field) => (
                        <Space
                          key={field.key}
                          align="baseline"
                          style={{ display: 'flex', marginBottom: 8, width: '100%' }}
                        >
                          <Form.Item
                            name={[field.name, 'giang_vien_id']}
                            rules={[{ required: true, message: 'Chọn giảng viên' }]}
                            style={{ marginBottom: 0, width: 280 }}
                          >
                            <Select
                              showSearch
                              placeholder="Giảng viên"
                              options={lecturerOptions}
                              filterOption={(input, option) =>
                                (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                              }
                            />
                          </Form.Item>
                          <Form.Item
                            name={[field.name, 'vai_tro']}
                            rules={[{ required: true, message: 'Chọn vai trò' }]}
                            style={{ marginBottom: 0, width: 140 }}
                          >
                            <Select options={VAI_TRO_OPTIONS} />
                          </Form.Item>
                          <Button
                            type="text"
                            danger
                            disabled={fields.length <= MIN_MEMBERS}
                            onClick={() => remove(field.name)}
                          >
                            Xóa
                          </Button>
                        </Space>
                      ))}
                      <Button
                        type="dashed"
                        block
                        disabled={fields.length >= MAX_MEMBERS}
                        onClick={() => add()}
                      >
                        Thêm thành viên
                      </Button>
                      <p style={{ marginTop: 8, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
                        3–5 thành viên, đúng 1 Chủ tịch
                      </p>
                    </>
                  )}
                </Form.List>

                <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                  <Tooltip
                    title={
                      hasScores
                        ? 'Hội đồng đã có điểm — chỉ thay được thành viên chưa chấm; không đổi ngày, giờ, phòng'
                        : undefined
                    }
                  >
                    <Button
                      type="primary"
                      loading={saveMutation.isPending}
                      onClick={() => void handleSave()}
                    >
                      Lưu hội đồng và lịch
                    </Button>
                  </Tooltip>
                  {!isNew && canDelete && (
                    <Popconfirm title="Xóa hội đồng này?" onConfirm={() => void handleDelete()}>
                      <Button danger loading={deleteMutation.isPending}>
                        Xóa hội đồng
                      </Button>
                    </Popconfirm>
                  )}
                </div>
              </Form>
            </Card>

            {committee && (
              <Card title="Sinh viên bảo vệ">
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <Select
                    showSearch
                    style={{ flex: 1 }}
                    placeholder="Thêm sinh viên"
                    value={selectedStudent}
                    onChange={(value: number) => setSelectedStudent(value)}
                    options={studentOptions}
                    filterOption={(input, option) =>
                      (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                    }
                  />
                  <Button
                    onClick={() => void handleAddStudent()}
                    disabled={selectedStudent === undefined}
                    loading={addScheduleMutation.isPending}
                  >
                    Thêm vào lịch
                  </Button>
                </div>
                <Table<ScheduleRow>
                  size="small"
                  rowKey="id"
                  pagination={false}
                  columns={scheduleColumns}
                  dataSource={committee.lich}
                  locale={{ emptyText: 'Chưa có sinh viên trong lịch' }}
                />
              </Card>
            )}
          </>
        )}
      </Col>
    </Row>
  )
}
