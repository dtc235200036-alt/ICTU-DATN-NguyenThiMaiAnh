import { useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Row,
  Skeleton,
  Steps,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import { Link, useSearchParams } from 'react-router'

import { DownloadError, downloadFile } from '../../api/download'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import { formatDateTime } from '../../utils/format'
import DocumentUpload from '../documents/DocumentUpload'
import { useOutline, useOutlines, useSubmitOutline } from './api'
import type { OutlineDetail } from './api'
import { tenFileHopLe, trangThaiDeCuong } from './constants'
import FinalReportTab from './FinalReportTab'
import VersionHistory from './VersionHistory'

// UC2.1 - E1: chỉ nộp được khi CHUA_NOP hoặc YEU_CAU_SUA.
const DISABLED_REASON: Record<string, string> = {
  CHO_DUYET: 'Đề cương đang chờ GVHD duyệt — bạn nộp được phiên bản mới khi được yêu cầu sửa.',
  GVHD_DA_DUYET: 'GVHD đã duyệt đề cương và sẽ nộp lên Bộ môn.',
  CHO_BO_MON_DUYET: 'Đề cương đang chờ Lãnh đạo bộ môn phê duyệt.',
  DA_DUYET: 'Đề cương đã được Bộ môn phê duyệt và nộp về khoa.',
}

const STEP_INDEX: Record<string, number> = {
  CHUA_NOP: 0,
  YEU_CAU_SUA: 0,
  CHO_DUYET: 1,
  GVHD_DA_DUYET: 2,
  CHO_BO_MON_DUYET: 3,
  DA_DUYET: 4,
}

const DEFAULT_TAB = 'de-cuong'

function OutlineSteps({ detail }: { detail: OutlineDetail }) {
  const current = STEP_INDEX[detail.trang_thai] ?? 0
  return (
    <Steps
      size="small"
      current={current}
      status={detail.trang_thai === 'YEU_CAU_SUA' ? 'error' : current === 4 ? 'finish' : 'process'}
      style={{ marginBottom: 20 }}
      items={[
        { title: 'Nộp đề cương' },
        { title: 'GVHD duyệt' },
        { title: 'GVHD nộp lên Bộ môn' },
        { title: 'Bộ môn phê duyệt' },
        { title: 'Đã nộp về khoa' },
      ]}
    />
  )
}

/**
 * SV "Nộp đề cương": tên đề tài + GVHD, tải file đề cương (kéo thả), ghi chú,
 * nộp; theo dõi các bước duyệt GVHD -> Bộ môn và lịch sử phiên bản. Tab "Báo
 * cáo cuối" giữ nguyên.
 */
export default function OutlinePage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') ?? DEFAULT_TAB
  const [ghiChu, setGhiChu] = useState('')

  const {
    data: outlinesPage,
    isLoading: isListLoading,
    isError: isListError,
    error: listError,
    refetch: refetchList,
  } = useOutlines({})
  const ownItem = outlinesPage?.items[0]
  const deTaiId = ownItem?.de_tai_id

  const {
    data: detail,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
    refetch: refetchDetail,
  } = useOutline(deTaiId)
  const submitMutation = useSubmitOutline()

  if (isListLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }
  if (isListError) {
    return (
      <Card>
        <QueryErrorAlert error={listError} onRetry={() => void refetchList()} />
      </Card>
    )
  }
  if (!ownItem || deTaiId === undefined) {
    return (
      <Card>
        <Empty description="Bạn chưa được giao đề tài">
          <Link to="/de-tai">Xem đề tài của tôi</Link>
        </Empty>
      </Card>
    )
  }
  if (isDetailError) {
    return (
      <Card>
        <QueryErrorAlert error={detailError} onRetry={() => void refetchDetail()} />
      </Card>
    )
  }
  if (isDetailLoading || !detail) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  const trangThai = trangThaiDeCuong(detail.trang_thai)
  const mau = detail.ten_file_mau ?? 'Hxx.MSSV.Họ tên.Lớp.pdf'

  const handleSubmit = async (file: File) => {
    await submitMutation.mutateAsync({ deTaiId, file, ghiChu: ghiChu.trim() || undefined })
    setGhiChu('')
    message.success('Đã nộp đề cương — hệ thống đang kiểm tra trùng lặp')
  }

  const handleDownload = async (id: number, name: string) => {
    try {
      await downloadFile(`/documents/${id}/download`, name)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  return (
    <Card title="Nộp đề cương">
      <Tabs
        activeKey={activeTab}
        onChange={(key) => {
          const next = new URLSearchParams(searchParams)
          next.set('tab', key)
          setSearchParams(next, { replace: true })
        }}
        items={[
          {
            key: 'de-cuong',
            label: 'Đề cương',
            children: (
              <div>
                <OutlineSteps detail={detail} />
                <Alert
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                  message="Lưu ý khi nộp đề cương"
                  description={
                    <div>
                      File PDF (khuyến khích) hoặc DOCX, tối đa 20 MB, đặt tên đúng mẫu:{' '}
                      <Typography.Text code copyable>
                        {mau}
                      </Typography.Text>
                    </div>
                  }
                />
                <Row gutter={20}>
                  <Col xs={24} lg={12}>
                    <Form layout="vertical">
                      <Form.Item label="Tên đề tài">
                        <Input value={detail.ten_de_tai} readOnly />
                      </Form.Item>
                      <Form.Item label="GVHD">
                        <Input value={detail.giang_vien?.ho_ten ?? '—'} readOnly />
                      </Form.Item>
                      <Form.Item label="Trạng thái">
                        <Tag color={trangThai.color}>{trangThai.label}</Tag>
                        {detail.ket_qua_bo_mon === 'TRA_LAI' && detail.trang_thai === 'YEU_CAU_SUA' && (
                          <Tag color="volcano">Bộ môn trả lại</Tag>
                        )}
                      </Form.Item>
                    </Form>
                    {detail.luot_duyet_bo_mon.map((r, idx) => (
                      <Alert
                        key={idx}
                        style={{ marginBottom: 8 }}
                        type={r.ket_qua === 'DA_DUYET' ? 'success' : 'warning'}
                        showIcon
                        message={`Bộ môn ${r.ket_qua === 'DA_DUYET' ? 'đã phê duyệt' : 'trả lại'} — ${formatDateTime(r.thoi_diem)}`}
                        description={
                          <div>
                            {r.nhan_xet && <div>{r.nhan_xet}</div>}
                            {r.tai_lieu_ky_so && (
                              <Button
                                type="link"
                                style={{ padding: 0 }}
                                onClick={() =>
                                  void handleDownload(r.tai_lieu_ky_so!.id, r.tai_lieu_ky_so!.ten_goc)
                                }
                              >
                                ⬇ Bản đề cương đã ký
                              </Button>
                            )}
                          </div>
                        }
                      />
                    ))}
                  </Col>
                  <Col xs={24} lg={12}>
                    <Typography.Text strong>Tải file đề cương</Typography.Text>
                    <div style={{ marginTop: 8 }}>
                      <DocumentUpload
                        disabled={!detail.quyen.nop}
                        disabledReason={DISABLED_REASON[detail.trang_thai]}
                        submitLabel="Nộp"
                        loading={submitMutation.isPending}
                        onSubmit={handleSubmit}
                        hint="Kéo thả file DOCX/PDF vào đây, tối đa 20 MB"
                        fileWarning={(file) =>
                          tenFileHopLe(file.name)
                            ? null
                            : `Tên file chưa đúng mẫu ${mau} — GVHD sẽ không nộp lên Bộ môn được.`
                        }
                        extra={
                          <div style={{ marginTop: 12 }}>
                            <Typography.Text strong>Ghi chú</Typography.Text>
                            <Input.TextArea
                              rows={3}
                              maxLength={2000}
                              style={{ marginTop: 8 }}
                              disabled={!detail.quyen.nop}
                              value={ghiChu}
                              onChange={(e) => setGhiChu(e.target.value)}
                              placeholder="Ghi chú gửi GVHD (không bắt buộc)"
                            />
                          </div>
                        }
                      />
                    </div>
                  </Col>
                </Row>
                <div style={{ marginTop: 24 }}>
                  <VersionHistory
                    versions={detail.phien_ban}
                    trangThai={detail.trang_thai}
                    docLabel="đề cương"
                  />
                </div>
              </div>
            ),
          },
          {
            key: 'bao-cao-cuoi',
            label: 'Báo cáo cuối',
            children: <FinalReportTab deTaiId={deTaiId} />,
          },
        ]}
      />
    </Card>
  )
}
