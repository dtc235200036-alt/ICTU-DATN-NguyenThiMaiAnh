import { App as AntApp, Button, Card, Input, Popconfirm, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link, useNavigate, useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useLecturers } from '../accounts/api'
import { useCohorts } from '../cohorts/api'
import { useAuthStore } from '../../stores/auth'
import { LINH_VUC_OPTIONS, TRANG_THAI_DE_TAI } from './constants'
import { useRegisterTopic, useTopics } from './api'
import type { PersonRef, TopicListItem } from './api'

const { Search } = Input

const TRANG_THAI_SELECT_OPTIONS = [
  { value: 'all', label: 'Tất cả' },
  ...Object.entries(TRANG_THAI_DE_TAI).map(([value, meta]) => ({ value, label: meta.label })),
]

function renderPerson(person: PersonRef | null): string {
  if (!person || !person.ho_ten) return '—'
  return person.ma ? `${person.ho_ten} (${person.ma})` : person.ho_ten
}

/**
 * MH-05 (UC1.4): danh sách đề tài lọc theo trạng thái/đợt/GVHD/lĩnh vực/từ
 * khóa, luôn trong phạm vi server-side của vai trò đang xem (T-02-29). Mọi bộ
 * lọc + trang sống trong URL (useSearchParams) để menu, reload và back/forward
 * đều giữ đúng góc nhìn hiện tại.
 */
export default function TopicListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const { message } = AntApp.useApp()
  const registerMutation = useRegisterTopic()

  const phamVi = searchParams.get('pham_vi') === 'cua_toi' ? 'cua_toi' : 'tat_ca'
  const dotDoAnId = searchParams.get('dot_do_an_id') ?? undefined
  const trangThai = searchParams.get('trang_thai') ?? undefined
  const giangVienId = searchParams.get('giang_vien_id') ?? undefined
  const linhVuc = searchParams.get('linh_vuc') ?? undefined
  const q = searchParams.get('q') ?? undefined
  const sapXep = searchParams.get('sap_xep') === 'ten' ? 'ten' : 'moi_nhat'
  const page = Number(searchParams.get('page') ?? '1') || 1
  const pageSize = Number(searchParams.get('page_size') ?? '10') || 10

  const { data: cohorts } = useCohorts()
  const { data: lecturers } = useLecturers()

  const { data, isFetching } = useTopics({
    dot_do_an_id: dotDoAnId ? Number(dotDoAnId) : undefined,
    trang_thai: trangThai,
    giang_vien_id: giangVienId ? Number(giangVienId) : undefined,
    linh_vuc: linhVuc,
    q,
    pham_vi: phamVi,
    sap_xep: sapXep,
    page,
    page_size: pageSize,
  })

  const updateParams = (patch: Record<string, string | undefined>, resetPage = true) => {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined || value === '' || value === 'all') {
        next.delete(key)
      } else {
        next.set(key, value)
      }
    }
    if (resetPage) {
      next.delete('page')
    }
    setSearchParams(next)
  }

  const canPropose = user?.vai_tro === 'SINH_VIEN' || user?.vai_tro === 'GIANG_VIEN'

  const handleRegister = async (record: TopicListItem) => {
    try {
      await registerMutation.mutateAsync(record.id)
      message.success('Đăng ký thành công — đề tài đang chờ Bộ môn duyệt')
      navigate(`/de-tai/${record.id}`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<TopicListItem> = [
    {
      title: 'Tên đề tài',
      dataIndex: 'ten_de_tai',
      sorter: true,
      sortOrder: sapXep === 'ten' ? 'ascend' : undefined,
      sortDirections: ['ascend'],
      render: (_value, record) => <Link to={`/de-tai/${record.id}`}>{record.ten_de_tai}</Link>,
    },
    {
      title: 'Lĩnh vực',
      dataIndex: 'linh_vuc',
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'Người đề xuất',
      dataIndex: 'nguoi_de_xuat',
      render: (person: PersonRef) => renderPerson(person),
    },
    {
      title: 'GVHD',
      dataIndex: 'giang_vien_huong_dan',
      render: (person: PersonRef | null) => renderPerson(person),
    },
    {
      title: 'Sinh viên',
      dataIndex: 'sinh_vien',
      render: (person: PersonRef | null) => renderPerson(person),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trang_thai',
      render: (value: string) => {
        const meta = TRANG_THAI_DE_TAI[value] ?? { label: value, color: 'default' }
        return <Tag color={meta.color}>{meta.label}</Tag>
      },
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button size="small" onClick={() => navigate(`/de-tai/${record.id}`)}>
            Xem
          </Button>
          {record.co_the_dang_ky && (
            <Popconfirm
              title="Đăng ký đề tài này?"
              description="Sau khi đăng ký, đề tài chuyển sang Chờ duyệt để Bộ môn xác nhận và phân công GVHD."
              onConfirm={() => handleRegister(record)}
            >
              <Button size="small" type="primary" loading={registerMutation.isPending}>
                Đăng ký
              </Button>
            </Popconfirm>
          )}
        </div>
      ),
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
        }}
      >
        <h2 style={{ margin: 0 }}>
          {phamVi === 'cua_toi' ? 'Đề tài của tôi' : 'Danh sách đề tài'}
        </h2>
        {canPropose && (
          <Button type="primary" onClick={() => navigate('/de-tai/de-xuat')}>
            Đề xuất đề tài
          </Button>
        )}
      </div>

      <Card>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ marginBottom: 4 }}>Đợt đồ án</div>
            <Select
              style={{ width: 220 }}
              value={dotDoAnId ? Number(dotDoAnId) : 'all'}
              onChange={(value) =>
                updateParams({ dot_do_an_id: value === 'all' ? undefined : String(value) })
              }
              options={[
                { value: 'all', label: 'Tất cả các đợt' },
                ...(cohorts ?? []).map((c) => ({
                  value: c.id,
                  label: `${c.ten_dot} (${c.khoa})`,
                })),
              ]}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}>Trạng thái</div>
            <Select
              style={{ width: 160 }}
              value={trangThai ?? 'all'}
              onChange={(value) =>
                updateParams({ trang_thai: value === 'all' ? undefined : value })
              }
              options={TRANG_THAI_SELECT_OPTIONS}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}>Giảng viên hướng dẫn</div>
            <Select
              showSearch
              style={{ width: 240 }}
              value={giangVienId ? Number(giangVienId) : 'all'}
              onChange={(value) =>
                updateParams({ giang_vien_id: value === 'all' ? undefined : String(value) })
              }
              filterOption={(input, option) =>
                (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
              }
              options={[
                { value: 'all', label: 'Tất cả' },
                ...(lecturers ?? []).map((gv) => ({
                  value: gv.id,
                  label: `${gv.hoc_vi ?? ''} ${gv.ho_ten ?? ''}`.trim(),
                })),
              ]}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}>Lĩnh vực</div>
            <Select
              style={{ width: 220 }}
              value={linhVuc ?? 'all'}
              onChange={(value) => updateParams({ linh_vuc: value === 'all' ? undefined : value })}
              options={[
                { value: 'all', label: 'Tất cả' },
                ...LINH_VUC_OPTIONS.map((v) => ({ value: v, label: v })),
              ]}
            />
          </div>
          <div style={{ minWidth: 240 }}>
            <div style={{ marginBottom: 4 }}>Tìm kiếm</div>
            <Search
              defaultValue={q}
              allowClear
              placeholder="Tìm theo tên đề tài..."
              onSearch={(value) => updateParams({ q: value || undefined })}
            />
          </div>
        </div>

        <Table<TopicListItem>
          rowKey="id"
          loading={isFetching}
          columns={columns}
          dataSource={data?.items ?? []}
          locale={{ emptyText: 'Chưa có đề tài phù hợp bộ lọc' }}
          onChange={(_pagination, _filters, sorter) => {
            const single = Array.isArray(sorter) ? sorter[0] : sorter
            updateParams({ sap_xep: single?.order ? 'ten' : undefined }, false)
          }}
          pagination={{
            current: page,
            pageSize,
            total: data?.total ?? 0,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              const next = new URLSearchParams(searchParams)
              next.set('page', String(nextPage))
              next.set('page_size', String(nextPageSize))
              setSearchParams(next)
            },
          }}
        />
      </Card>
    </div>
  )
}
