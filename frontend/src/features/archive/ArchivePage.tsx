import { useState } from 'react'
import {
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Drawer,
  Input,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { DownloadError, downloadFile } from '../../api/download'
import { useAuthStore } from '../../stores/auth'
import { formatBytes } from '../../utils/format'
import { useLecturers } from '../accounts/api'
import type { PersonRef } from '../topics/api'
import ArchiveFormModal from './ArchiveFormModal'
import ArchiveImportModal from './ArchiveImportModal'
import {
  useArchive,
  useArchiveKhoa,
  useArchiveRecord,
  useDeleteArchive,
  useReindexArchive,
} from './api'
import type { ArchiveListItem, ArchiveStudent, TrangThaiIndex } from './api'

const { Search } = Input

const NGUON_LABEL: Record<string, string> = {
  HE_THONG: 'Hệ thống (chốt bảo vệ)',
  IMPORT: 'Import khóa cũ',
}

function renderStudent(sv: ArchiveStudent | null): string {
  if (!sv || (!sv.ho_ten && !sv.ma)) return '—'
  if (sv.ho_ten && sv.ma) return `${sv.ho_ten} (${sv.ma})`
  return sv.ho_ten ?? sv.ma ?? '—'
}

function renderPerson(person: PersonRef | null): string {
  if (!person || !person.ho_ten) return '—'
  return person.ho_ten
}

function renderDiem(diem: number | null): string {
  return diem === null ? '—' : diem.toFixed(2).replace(/0$/, '')
}

function splitKeywords(tuKhoa: string | null): string[] {
  if (!tuKhoa) return []
  return tuKhoa
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0)
}

function IndexTag({ value }: { value: TrangThaiIndex }) {
  return value === 'DA_INDEX' ? (
    <Tag color="green">Đã index</Tag>
  ) : (
    <Tag color="orange">Chưa index</Tag>
  )
}

/**
 * MH-13 (UC5.1/UC5.3/UC5.4): mọi vai trò tra cứu kho đồ án theo khóa, GVHD,
 * từ khóa (bộ lọc + trang + bản ghi đang mở sống trong URL) và mở Drawer
 * "Chi tiết bản ghi kho" để tải báo cáo cuối. Chỉ Bộ môn thấy cột Chỉ mục AI
 * và các thao tác thêm/sửa/xóa/index lại/import (server vẫn chặn 403).
 */
export default function ArchivePage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const user = useAuthStore((s) => s.user)
  const isBoMon = user?.vai_tro === 'BO_MON'
  // WR-10: server không trả điểm của SV khác cho vai trò Sinh viên.
  const isSinhVien = user?.vai_tro === 'SINH_VIEN'

  const khoa = searchParams.get('khoa') ?? undefined
  const giangVienId = searchParams.get('giang_vien_id') ?? undefined
  const q = searchParams.get('q') ?? undefined
  const page = Number(searchParams.get('page') ?? '1') || 1
  const pageSize = Number(searchParams.get('page_size') ?? '10') || 10
  const openIdRaw = Number(searchParams.get('id') ?? '')
  const openId = Number.isInteger(openIdRaw) && openIdRaw > 0 ? openIdRaw : undefined

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [importOpen, setImportOpen] = useState(false)

  const { data: khoaOptions } = useArchiveKhoa()
  const { data: lecturers } = useLecturers()
  const { data, isFetching } = useArchive({
    khoa,
    giang_vien_id: giangVienId ? Number(giangVienId) : undefined,
    q,
    page,
    page_size: pageSize,
  })
  const { data: detail, isError: detailError } = useArchiveRecord(openId)
  const deleteMutation = useDeleteArchive()
  const reindexMutation = useReindexArchive()

  const updateParams = (patch: Record<string, string | undefined>, resetPage = true) => {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined || value === '' || value === 'all') {
        next.delete(key)
      } else {
        next.set(key, value)
      }
    }
    if (resetPage) next.delete('page')
    setSearchParams(next)
  }

  const openRecord = (id: number) => updateParams({ id: String(id) }, false)
  const closeDrawer = () => updateParams({ id: undefined }, false)

  const handleDownload = async () => {
    if (!detail?.file) return
    try {
      await downloadFile(`/archive/${detail.id}/file`, detail.file.ten_goc)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : getErrorMessage(err))
    }
  }

  const handleDelete = async () => {
    if (!detail) return
    try {
      await deleteMutation.mutateAsync(detail.id)
      message.success('Đã xóa bản ghi khỏi kho')
      closeDrawer()
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleReindex = async () => {
    if (!detail) return
    try {
      await reindexMutation.mutateAsync(detail.id)
      message.success('Đã gửi yêu cầu index lại — trạng thái cập nhật sau ít giây')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<ArchiveListItem> = [
    {
      title: 'Tên đề tài',
      dataIndex: 'ten_de_tai',
      render: (_value, record) => (
        <Button type="link" style={{ padding: 0, whiteSpace: 'normal', textAlign: 'left', height: 'auto' }} onClick={() => openRecord(record.id)}>
          {record.ten_de_tai}
        </Button>
      ),
    },
    {
      title: 'Sinh viên',
      dataIndex: 'sinh_vien',
      render: (sv: ArchiveStudent | null) => (sv?.ho_ten ?? sv?.ma ?? '—'),
    },
    {
      title: 'Khóa',
      dataIndex: 'khoa',
      width: 80,
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'GVHD',
      dataIndex: 'giang_vien',
      render: (person: PersonRef | null) => renderPerson(person),
    },
    {
      title: 'Điểm',
      dataIndex: 'diem',
      width: 80,
      render: (value: number | null) => renderDiem(value),
    },
    {
      title: 'Từ khóa',
      dataIndex: 'tu_khoa',
      render: (value: string | null) => {
        const words = splitKeywords(value)
        if (words.length === 0) return '—'
        return (
          <Space size={[0, 4]} wrap>
            {words.map((w) => (
              <Tag key={w}>{w}</Tag>
            ))}
          </Space>
        )
      },
    },
  ]
  if (isSinhVien) {
    const diemIdx = columns.findIndex((col) => 'dataIndex' in col && col.dataIndex === 'diem')
    if (diemIdx >= 0) columns.splice(diemIdx, 1)
  }

  if (isBoMon) {
    columns.push({
      title: 'Chỉ mục AI',
      dataIndex: 'trang_thai_index',
      width: 120,
      render: (value: TrangThaiIndex) => <IndexTag value={value} />,
    })
  }

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
        <h2 style={{ margin: 0 }}>Kho đồ án</h2>
        {isBoMon && (
          <Space>
            <Button onClick={() => setImportOpen(true)}>Import khóa cũ</Button>
            <Button
              type="primary"
              onClick={() => {
                setEditing(false)
                setFormOpen(true)
              }}
            >
              Thêm bản ghi
            </Button>
          </Space>
        )}
      </div>

      <Card>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ marginBottom: 4 }}>Khóa</div>
            <Select
              style={{ width: 140 }}
              value={khoa ?? 'all'}
              onChange={(value) => updateParams({ khoa: value === 'all' ? undefined : value })}
              options={[
                { value: 'all', label: 'Tất cả' },
                ...(khoaOptions ?? []).map((k) => ({ value: k, label: k })),
              ]}
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
          <div style={{ minWidth: 280 }}>
            <div style={{ marginBottom: 4 }}>Từ khóa</div>
            <Search
              key={q ?? ''}
              defaultValue={q}
              allowClear
              placeholder="Tên đề tài hoặc từ khóa"
              onSearch={(value) => updateParams({ q: value.trim() || undefined })}
            />
          </div>
        </div>

        <Table<ArchiveListItem>
          rowKey="id"
          loading={isFetching}
          columns={columns}
          dataSource={data?.items ?? []}
          locale={{ emptyText: 'Chưa có đồ án phù hợp bộ lọc' }}
          pagination={{
            current: page,
            pageSize,
            total: data?.total ?? 0,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              updateParams(
                {
                  page: nextPage > 1 ? String(nextPage) : undefined,
                  page_size: nextPageSize !== 10 ? String(nextPageSize) : undefined,
                },
                false,
              )
            },
          }}
        />
      </Card>

      <Drawer
        open={openId !== undefined}
        width={520}
        title="Chi tiết bản ghi kho"
        onClose={closeDrawer}
        footer={
          isBoMon && detail ? (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <Popconfirm
                title="Xóa bản ghi khỏi kho?"
                description="Lịch sử kết quả kiểm tra trùng lặp đã ghi nhận vẫn được giữ (UC5.3 - E1)."
                okText="Xóa"
                cancelText="Hủy"
                okButtonProps={{ danger: true }}
                onConfirm={handleDelete}
              >
                <Button danger loading={deleteMutation.isPending}>
                  Xóa
                </Button>
              </Popconfirm>
              {detail.trang_thai_index === 'CHUA_INDEX' && (
                <Button loading={reindexMutation.isPending} onClick={handleReindex}>
                  Index lại
                </Button>
              )}
              <Button
                type="primary"
                onClick={() => {
                  setEditing(true)
                  setFormOpen(true)
                }}
              >
                Sửa
              </Button>
            </div>
          ) : null
        }
      >
        {detailError && <div>Không tìm thấy bản ghi kho</div>}
        {detail && (
          <div>
            <h3 style={{ marginTop: 0 }}>{detail.ten_de_tai}</h3>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Sinh viên">{renderStudent(detail.sinh_vien)}</Descriptions.Item>
              <Descriptions.Item label="Khóa">{detail.khoa ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="GVHD">{renderPerson(detail.giang_vien)}</Descriptions.Item>
              <Descriptions.Item label="Điểm bảo vệ">{renderDiem(detail.diem)}</Descriptions.Item>
              <Descriptions.Item label="Từ khóa">
                {splitKeywords(detail.tu_khoa).join(', ') || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Nguồn">{NGUON_LABEL[detail.nguon] ?? detail.nguon}</Descriptions.Item>
              {isBoMon && (
                <Descriptions.Item label="Trạng thái chỉ mục AI">
                  <IndexTag value={detail.trang_thai_index} />
                </Descriptions.Item>
              )}
            </Descriptions>
            {detail.file && (
              <Button style={{ marginTop: 16 }} onClick={handleDownload}>
                {`⬇ Tải báo cáo cuối (${detail.file.dinh_dang}, ${formatBytes(detail.file.kich_thuoc)})`}
              </Button>
            )}
          </div>
        )}
      </Drawer>

      <ArchiveFormModal
        open={formOpen}
        record={editing ? detail : undefined}
        onClose={() => setFormOpen(false)}
        onSaved={(saved) => openRecord(saved.id)}
      />
      <ArchiveImportModal open={importOpen} onClose={() => setImportOpen(false)} />
    </div>
  )
}
