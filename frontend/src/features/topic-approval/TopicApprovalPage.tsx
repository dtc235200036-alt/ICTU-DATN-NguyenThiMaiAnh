import { useState } from 'react'
import { App as AntApp, Alert, Button, Card, Drawer, Input, Modal, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { getErrorMessage } from '../../api/client'
import { useLecturers } from '../accounts/api'
import { useCohorts } from '../cohorts/api'
import { useTopic } from '../topics/api'
import type { PersonRef, SavedChiTietTrungLap } from '../topics/api'
import { useApproveTopic, usePendingTopics, useRejectTopic } from './api'
import type { PendingTopicItem, TitleCheckSummary } from './api'

const { TextArea } = Input

function renderPerson(person: PersonRef | null): string {
  if (!person || !person.ho_ten) return '—'
  return person.ma ? `${person.ho_ten} (${person.ma})` : person.ho_ten
}

function renderKiemTraTag(summary: TitleCheckSummary) {
  if (summary.trang_thai === 'CO_TUONG_TU') {
    return <Tag color="warning">{summary.so_tuong_tu} đề tài tương tự</Tag>
  }
  if (summary.trang_thai === 'KHONG_TRUNG') {
    return <Tag color="success">Không trùng</Tag>
  }
  return <Tag>Chưa kiểm tra</Tag>
}

function formatNgayDeXuat(iso: string | null): string {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    dateStyle: 'short',
  }).format(new Date(iso))
}

const chiTietColumns: ColumnsType<SavedChiTietTrungLap> = [
  { title: 'Tên đề tài', dataIndex: 'doi_tuong_trung' },
  { title: 'Tỷ lệ', dataIndex: 'ty_le', render: (ty_le: number) => `${ty_le}%` },
]

/**
 * MH-07/UC1.3: bảng "Đề tài chờ duyệt" + Drawer chi tiết (kết quả kiểm tra
 * tên đã lưu, chọn GVHD) + Modal "Từ chối đề tài". Bộ môn duyệt (mở đăng ký
 * khi chưa có SV), duyệt và phân công GVHD thủ công (khi đã có SV — không
 * bao giờ tự động chọn, UC1.3 E1), hoặc từ chối kèm lý do bắt buộc.
 */
export default function TopicApprovalPage() {
  const { message } = AntApp.useApp()

  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [openId, setOpenId] = useState<number | undefined>(undefined)
  const [selectedGv, setSelectedGv] = useState<number | undefined>(undefined)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const { data: cohorts } = useCohorts()
  const { data: lecturers } = useLecturers()
  const { data, isFetching } = usePendingTopics({
    dot_do_an_id: dotDoAnId,
    page,
    page_size: pageSize,
  })
  const { data: detail } = useTopic(openId)
  const approveMutation = useApproveTopic()
  const rejectMutation = useRejectTopic()

  const hasSv = detail?.sinh_vien != null

  const closeDrawer = () => {
    setOpenId(undefined)
    setSelectedGv(undefined)
    setRejectOpen(false)
    setRejectReason('')
  }

  const handleApprove = async () => {
    if (openId === undefined) return
    try {
      await approveMutation.mutateAsync({ id: openId, giang_vien_id: selectedGv ?? null })
      message.success(hasSv ? 'Đã duyệt và phân công GVHD' : 'Đã duyệt đề tài')
      closeDrawer()
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleReject = async () => {
    if (openId === undefined) return
    try {
      await rejectMutation.mutateAsync({ id: openId, ly_do: rejectReason })
      message.success('Đã từ chối đề tài')
      closeDrawer()
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const columns: ColumnsType<PendingTopicItem> = [
    { title: 'Tên đề tài', dataIndex: 'ten_de_tai' },
    {
      title: 'Người đề xuất',
      dataIndex: 'nguoi_de_xuat',
      render: (person: PersonRef) => renderPerson(person),
    },
    { title: 'Lĩnh vực', dataIndex: 'linh_vuc', render: (value: string | null) => value ?? '—' },
    {
      title: 'Ngày đề xuất',
      dataIndex: 'ngay_de_xuat',
      render: (value: string | null) => formatNgayDeXuat(value),
    },
    {
      title: 'Kiểm tra tên',
      dataIndex: 'kiem_tra_ten',
      render: (summary: TitleCheckSummary) => renderKiemTraTag(summary),
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) =>
        openId === record.id ? (
          <Button size="small" type="primary" disabled>
            Đang xem
          </Button>
        ) : (
          <Button size="small" onClick={() => setOpenId(record.id)}>
            Xem chi tiết
          </Button>
        ),
    },
  ]

  return (
    <div>
      <Card
        title="Đề tài chờ duyệt"
        extra={
          <Select
            allowClear
            placeholder="Tất cả các đợt"
            style={{ width: 260 }}
            value={dotDoAnId}
            onChange={(value: number | undefined) => {
              setDotDoAnId(value)
              setPage(1)
            }}
            options={(cohorts ?? []).map((c) => ({
              value: c.id,
              label: `${c.ten_dot} (${c.khoa})`,
            }))}
          />
        }
      >
        <Table<PendingTopicItem>
          rowKey="id"
          loading={isFetching}
          columns={columns}
          dataSource={data?.items ?? []}
          locale={{ emptyText: 'Không có đề tài chờ duyệt' }}
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
      </Card>

      <Drawer
        width={560}
        title="Chi tiết đề tài chờ duyệt"
        open={openId !== undefined}
        onClose={closeDrawer}
        footer={
          detail && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <Button danger onClick={() => setRejectOpen(true)}>
                Từ chối
              </Button>
              <Button
                type="primary"
                disabled={hasSv && selectedGv === undefined}
                loading={approveMutation.isPending}
                onClick={handleApprove}
              >
                {hasSv ? 'Duyệt và phân công' : 'Duyệt'}
              </Button>
            </div>
          )
        }
      >
        {detail && (
          <>
            <h2 style={{ margin: '0 0 4px', fontSize: 15 }}>{detail.ten_de_tai}</h2>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
              Người đề xuất: {renderPerson(detail.nguoi_de_xuat)} · Lĩnh vực:{' '}
              {detail.linh_vuc ?? '—'} · Đợt {detail.dot_do_an.ten_dot}
            </p>
            <p style={{ margin: '0 0 16px', fontSize: 13 }}>{detail.mo_ta ?? '—'}</p>

            {detail.kiem_tra_ten && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 20 }}
                message="Kết quả kiểm tra tên đã lưu lúc đề xuất (UC0.6)"
                description={
                  detail.kiem_tra_ten.chi_tiet.length > 0 ? (
                    <Table<SavedChiTietTrungLap>
                      size="small"
                      rowKey="doi_tuong_trung"
                      pagination={false}
                      style={{ marginTop: 8 }}
                      columns={chiTietColumns}
                      dataSource={detail.kiem_tra_ten.chi_tiet}
                    />
                  ) : detail.kiem_tra_ten.trang_thai === 'LOI' ? (
                    <Tag>Chưa kiểm tra</Tag>
                  ) : (
                    <Tag color="success">Không trùng</Tag>
                  )
                }
              />
            )}

            {hasSv ? (
              <div style={{ marginBottom: 20 }}>
                <p style={{ marginBottom: 8 }}>Sinh viên: {renderPerson(detail.sinh_vien)}</p>
                <div className="ant-form-item-label" style={{ marginBottom: 4 }}>
                  Giảng viên hướng dẫn
                </div>
                <Select
                  showSearch
                  style={{ width: '100%' }}
                  placeholder="Chọn giảng viên hướng dẫn"
                  value={selectedGv}
                  onChange={(value: number) => setSelectedGv(value)}
                  filterOption={(input, option) =>
                    (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                  options={(lecturers ?? []).map((gv) => ({
                    value: gv.id,
                    label:
                      detail.loai_nguoi_de_xuat === 'GIANG_VIEN' &&
                      detail.nguoi_de_xuat.id === gv.id
                        ? `${gv.ho_ten ?? ''} (người đề xuất)`
                        : (gv.ho_ten ?? ''),
                  }))}
                />
                <p style={{ marginTop: 8, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
                  Bộ môn vẫn phải xác nhận thủ công kể cả khi GV đề xuất là người phù hợp duy nhất
                  (UC1.3 - E1).
                </p>
              </div>
            ) : (
              <p style={{ marginBottom: 20 }}>
                Đề tài do GV đề xuất, chưa có sinh viên — duyệt để mở cho sinh viên đăng ký.
              </p>
            )}
          </>
        )}
      </Drawer>

      <Modal
        title="Từ chối đề tài"
        open={rejectOpen}
        onCancel={() => setRejectOpen(false)}
        okText="Xác nhận từ chối"
        cancelText="Hủy"
        okButtonProps={{
          danger: true,
          disabled: rejectReason.trim().length === 0,
          loading: rejectMutation.isPending,
        }}
        onOk={handleReject}
      >
        <p style={{ margin: '0 0 12px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
          Đề tài: {detail?.ten_de_tai ?? ''}
        </p>
        <div style={{ marginBottom: 4 }}>Lý do từ chối</div>
        <TextArea
          rows={3}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Nhập lý do để người đề xuất biết cách chỉnh sửa..."
        />
      </Modal>
    </div>
  )
}
