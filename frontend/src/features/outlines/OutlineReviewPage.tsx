import { useEffect, useState } from 'react'
import { App as AntApp, Alert, Button, Card, Col, Form, Input, Popconfirm, Row, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { DownloadError, downloadFile } from '../../api/download'
import { useAuthStore } from '../../stores/auth'
import { formatBytes, formatDate } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import CheckPanel from '../documents/CheckPanel'
import CheckStatusTag from '../documents/CheckStatusTag'
import { useOutline, useOutlines, useReviewOutline } from './api'
import type { OutlineListItem, OutlineTrangThai, OutlineVersion } from './api'
import VersionHistory from './VersionHistory'

const { TextArea } = Input

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

const STATUS_OPTIONS: { value: OutlineTrangThai; label: string }[] = [
  { value: 'CHUA_NOP', label: 'Chưa nộp' },
  { value: 'CHO_DUYET', label: 'Chờ duyệt' },
  { value: 'YEU_CAU_SUA', label: 'Yêu cầu sửa' },
  { value: 'DA_DUYET', label: 'Đã duyệt' },
]

function versionLabel(version: OutlineVersion, isNewest: boolean): string {
  const base = `v${version.tai_lieu.so_phien_ban} - nộp ${formatDate(version.tai_lieu.thoi_diem_nop)}`
  return isNewest ? `${base} (mới nhất)` : base
}

/**
 * MH-09/UC2.2: GVHD chọn một đề tài từ bảng (hoặc ?de_tai_id= trên URL), xem
 * từng phiên bản kèm panel kiểm tra trùng lặp sống, rồi duyệt/yêu cầu sửa.
 * Bộ môn dùng chung màn hình ở chế độ chỉ đọc (API tự chặn review — T-03-13).
 */
export default function OutlineReviewPage() {
  const { message } = AntApp.useApp()
  const user = useAuthStore((state) => state.user)
  const isBoMon = user?.vai_tro === 'BO_MON'

  const [searchParams, setSearchParams] = useSearchParams()
  const deTaiIdParam = searchParams.get('de_tai_id')
  const selectedId = deTaiIdParam ? Number(deTaiIdParam) : undefined
  const trangThaiParam = searchParams.get('trang_thai') as OutlineTrangThai | null
  const trangThaiFilter: OutlineTrangThai | undefined =
    trangThaiParam ?? (isBoMon ? undefined : 'CHO_DUYET')

  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>(undefined)
  const [nhanXet, setNhanXet] = useState('')

  const { data: outlinesPage, isFetching: isListFetching } = useOutlines({
    trang_thai: trangThaiFilter,
  })
  const {
    data: detail,
    isError: isDetailError,
    error: detailError,
    refetch: refetchDetail,
  } = useOutline(selectedId)
  const reviewMutation = useReviewOutline()

  useEffect(() => {
    if (detail) {
      setSelectedVersionId(detail.phien_ban[0]?.tai_lieu.id)
      setNhanXet('')
    }
  }, [detail?.de_tai_id])

  const setTrangThaiFilter = (value: OutlineTrangThai | undefined) => {
    const next = new URLSearchParams(searchParams)
    if (value) {
      next.set('trang_thai', value)
    } else {
      next.delete('trang_thai')
    }
    setSearchParams(next, { replace: true })
  }

  const openDetail = (deTaiId: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('de_tai_id', String(deTaiId))
    setSearchParams(next, { replace: true })
  }

  const closeDetail = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('de_tai_id')
    setSearchParams(next, { replace: true })
  }

  const selectedVersion = detail?.phien_ban.find((v) => v.tai_lieu.id === selectedVersionId)
  const isNewestSelected = detail?.phien_ban[0]?.tai_lieu.id === selectedVersionId
  const canReview = Boolean(detail?.quyen.duyet) && isNewestSelected

  const handleDownload = async (version: OutlineVersion) => {
    try {
      await downloadFile(`/documents/${version.tai_lieu.id}/download`, version.tai_lieu.ten_goc)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  const submitReview = async (ketQua: 'DA_DUYET' | 'YEU_CAU_SUA') => {
    if (selectedId === undefined || selectedVersion === undefined) return
    if (ketQua === 'YEU_CAU_SUA' && nhanXet.trim().length === 0) {
      message.error('Vui lòng nhập nhận xét khi yêu cầu sửa')
      return
    }
    try {
      await reviewMutation.mutateAsync({
        deTaiId: selectedId,
        taiLieuDoAnId: selectedVersion.tai_lieu.id,
        ketQua,
        nhanXet: nhanXet.trim() || undefined,
      })
      message.success(ketQua === 'DA_DUYET' ? 'Đã duyệt đề cương' : 'Đã yêu cầu sửa')
      setNhanXet('')
    } catch (err) {
      message.error(getErrorMessage(err))
    } finally {
      void refetchDetail()
    }
  }

  const columns: ColumnsType<OutlineListItem> = [
    {
      title: 'Sinh viên',
      key: 'sinh_vien',
      render: (_value, record) =>
        record.sinh_vien
          ? `${record.sinh_vien.ho_ten}${record.sinh_vien.ma ? ` (${record.sinh_vien.ma})` : ''}`
          : '—',
    },
    { title: 'Đề tài', dataIndex: 'ten_de_tai' },
    {
      title: 'Phiên bản mới nhất',
      key: 'phien_ban_moi_nhat',
      render: (_value, record) =>
        record.phien_ban_moi_nhat
          ? `v${record.phien_ban_moi_nhat.so_phien_ban} · ${formatDate(
              record.phien_ban_moi_nhat.thoi_diem_nop,
            )}`
          : '—',
    },
    {
      title: 'Kiểm tra trùng lặp',
      key: 'kiem_tra',
      render: (_value, record) => <CheckStatusTag kiemTra={record.kiem_tra} />,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trang_thai',
      render: (value: string) => {
        const info = TRANG_THAI_LABEL[value] ?? { label: value, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => (
        <Button size="small" onClick={() => openDetail(record.de_tai_id)}>
          {!isBoMon && record.trang_thai === 'CHO_DUYET' ? 'Duyệt' : 'Xem'}
        </Button>
      ),
    },
  ]

  if (selectedId !== undefined && isDetailError) {
    const status = detailError instanceof AxiosError ? detailError.response?.status : undefined
    if (status === 403) {
      return <ForbiddenPage />
    }
  }

  return (
    <div>
      {selectedId === undefined ? (
        <Card
          title={isBoMon ? 'Đề cương toàn khoa' : 'Đề cương sinh viên hướng dẫn'}
          extra={
            <Select
              allowClear
              placeholder="Tất cả"
              style={{ width: 200 }}
              value={trangThaiFilter}
              onChange={(value: OutlineTrangThai | undefined) => setTrangThaiFilter(value)}
              options={STATUS_OPTIONS}
            />
          }
        >
          <Table<OutlineListItem>
            rowKey="de_tai_id"
            loading={isListFetching}
            columns={columns}
            dataSource={outlinesPage?.items ?? []}
            locale={{ emptyText: 'Không có đề cương nào ở trạng thái này' }}
            pagination={false}
          />
        </Card>
      ) : (
        <div>
          <Button style={{ marginBottom: 16 }} onClick={closeDetail}>
            ← Danh sách đề cương
          </Button>

          {detail && (
            <>
              <Row gutter={20}>
                <Col xs={24} lg={14}>
                  <Card
                    title={`Duyệt đề cương - ${detail.sinh_vien?.ho_ten ?? '—'}`}
                    extra={detail.ten_de_tai}
                  >
                    <Form layout="vertical">
                      <Form.Item label="Phiên bản">
                        <Select
                          style={{ width: '100%' }}
                          value={selectedVersionId}
                          onChange={(value: number) => setSelectedVersionId(value)}
                          options={detail.phien_ban.map((v, idx) => ({
                            value: v.tai_lieu.id,
                            label: versionLabel(v, idx === 0),
                          }))}
                        />
                      </Form.Item>
                    </Form>

                    {selectedVersion && (
                      <>
                        <p style={{ margin: '0 0 16px' }}>
                          <Button
                            type="link"
                            style={{ padding: 0, fontSize: 13 }}
                            onClick={() => void handleDownload(selectedVersion)}
                          >
                            ⬇ Tải file đề cương ({selectedVersion.tai_lieu.dinh_dang},{' '}
                            {formatBytes(selectedVersion.tai_lieu.kich_thuoc)})
                          </Button>
                        </p>

                        <p style={{ margin: '0 0 6px', fontSize: 13, fontWeight: 500 }}>
                          Tóm tắt nội dung đã trích xuất
                        </p>
                        {selectedVersion.tai_lieu.trich_xuat_loi ? (
                          <Alert
                            type="warning"
                            showIcon
                            message="Không trích xuất được nội dung — vui lòng tải file để xem (D-03)"
                            style={{ marginBottom: 16 }}
                          />
                        ) : (
                          <p
                            style={{
                              margin: '0 0 16px',
                              fontSize: 13,
                              color: 'rgba(0,0,0,0.65)',
                            }}
                          >
                            {selectedVersion.tai_lieu.tom_tat ?? '—'}
                          </p>
                        )}

                        {selectedVersion.luot_duyet && (
                          <Alert
                            type={selectedVersion.luot_duyet.ket_qua === 'DA_DUYET' ? 'success' : 'warning'}
                            showIcon
                            style={{ marginBottom: 16 }}
                            message={
                              selectedVersion.luot_duyet.ket_qua === 'DA_DUYET'
                                ? 'Đã duyệt'
                                : 'Yêu cầu sửa'
                            }
                            description={
                              <>
                                {selectedVersion.luot_duyet.nhan_xet} —{' '}
                                {formatDate(selectedVersion.luot_duyet.thoi_diem)}
                              </>
                            }
                          />
                        )}

                        {canReview && (
                          <Form layout="vertical">
                            <Form.Item label="Nhận xét">
                              <TextArea
                                rows={4}
                                maxLength={5000}
                                value={nhanXet}
                                onChange={(e) => setNhanXet(e.target.value)}
                              />
                            </Form.Item>
                            <div style={{ display: 'flex', gap: 8 }}>
                              <Button
                                danger
                                disabled={nhanXet.trim().length === 0}
                                loading={reviewMutation.isPending}
                                onClick={() => void submitReview('YEU_CAU_SUA')}
                              >
                                Yêu cầu sửa
                              </Button>
                              <Popconfirm
                                title="Duyệt đề cương này?"
                                onConfirm={() => void submitReview('DA_DUYET')}
                              >
                                <Button type="primary" loading={reviewMutation.isPending}>
                                  Duyệt đề cương
                                </Button>
                              </Popconfirm>
                            </div>
                          </Form>
                        )}
                      </>
                    )}
                  </Card>
                </Col>
                <Col xs={24} lg={10}>
                  <CheckPanel taiLieuId={selectedVersion?.tai_lieu.id} canRecheck />
                </Col>
              </Row>

              <div style={{ marginTop: 20 }}>
                <VersionHistory
                  versions={detail.phien_ban}
                  trangThai={detail.trang_thai}
                  docLabel="đề cương"
                />
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
