import { useEffect, useState } from 'react'
import { App as AntApp, Alert, Button, Card, Drawer, Input, Modal, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
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
  // DD/MM/YYYY (Asia/Ho_Chi_Minh) — dateStyle:'short' rút gọn năm còn 2 chữ số.
  return new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(iso))
}

const chiTietColumns: ColumnsType<SavedChiTietTrungLap> = [
  { title: 'Tên đề tài', dataIndex: 'doi_tuong_trung' },
  { title: 'Tỷ lệ', dataIndex: 'ty_le', render: (ty_le: number) => `${ty_le}%` },
]

/**
 * MH-07/UC1.3 (đổi ở 0015): GVHD xem đề tài SV trong lớp mình gửi lên — bảng
 * "Đề tài chờ duyệt" + Drawer chi tiết (kết quả kiểm tra tên đã lưu) + Modal
 * "Từ chối đề tài". Duyệt -> Đã phân công (SV bắt đầu nộp đề cương); từ chối
 * kèm lý do bắt buộc -> SV đề xuất lại đề tài khác.
 */
export default function TopicApprovalPage() {
  const { message } = AntApp.useApp()

  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [searchParams] = useSearchParams()
  const [openId, setOpenId] = useState<number | undefined>(undefined)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const { data: cohorts } = useCohorts()
  const { data, isFetching } = usePendingTopics({
    dot_do_an_id: dotDoAnId,
    page,
    page_size: pageSize,
  })
  const { data: detail } = useTopic(openId)
  const approveMutation = useApproveTopic()
  const rejectMutation = useRejectTopic()

  // Liên kết từ "Việc cần xử lý"/thông báo: /duyet-de-tai?de_tai_id=… mở sẵn Drawer.
  useEffect(() => {
    const fromLink = Number(searchParams.get('de_tai_id'))
    if (Number.isInteger(fromLink) && fromLink > 0) {
      setOpenId(fromLink)
    }
  }, [searchParams])

  const closeDrawer = () => {
    setOpenId(undefined)
    setRejectOpen(false)
    setRejectReason('')
  }

  const handleApprove = async () => {
    if (openId === undefined) return
    try {
      await approveMutation.mutateAsync(openId)
      message.success('Đã duyệt đề tài — sinh viên có thể nộp đề cương')
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
      title: 'Sinh viên',
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
                disabled={detail.trang_thai !== 'CHO_DUYET'}
                loading={approveMutation.isPending}
                onClick={handleApprove}
              >
                Duyệt đề tài
              </Button>
            </div>
          )
        }
      >
        {detail && (
          <>
            <h2 style={{ margin: '0 0 4px', fontSize: 15 }}>{detail.ten_de_tai}</h2>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
              Sinh viên: {renderPerson(detail.nguoi_de_xuat)} · Lĩnh vực:{' '}
              {detail.linh_vuc ?? '—'} · Đợt {detail.dot_do_an.khoa}
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

            {detail.trang_thai !== 'CHO_DUYET' && (
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 20 }}
                message="Đề tài không còn ở trạng thái Chờ duyệt"
              />
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
          placeholder="Nhập lý do để sinh viên biết cách chỉnh sửa hoặc đề xuất lại..."
        />
      </Modal>
    </div>
  )
}
