import { App as AntApp, Card, Empty, Skeleton, Tabs, Tag } from 'antd'
import { Link, useSearchParams } from 'react-router'

import QueryErrorAlert from '../../components/QueryErrorAlert'
import DocumentUpload from '../documents/DocumentUpload'
import { useOutline, useOutlines, useSubmitOutline } from './api'
import FinalReportTab from './FinalReportTab'
import VersionHistory from './VersionHistory'

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

// UC2.1 - E1: chỉ nộp được khi CHUA_NOP hoặc YEU_CAU_SUA; hai lý do còn lại
// (đang chờ duyệt / đã duyệt) hiển thị nguyên văn ở Alert của DocumentUpload.
const DISABLED_REASON: Record<string, string> = {
  CHO_DUYET: 'Đề cương đang chờ GVHD duyệt — bạn nộp được phiên bản mới khi GVHD yêu cầu sửa.',
  DA_DUYET: 'Đề cương đã được duyệt.',
}

const DEFAULT_TAB = 'de-cuong'

/**
 * MH-08 (SV): Tabs "Đề cương" / "Báo cáo cuối" (khóa key trên URL `?tab=` —
 * tab 'bao-cao-cuoi' được plan 03-03 thêm vào items, không sửa page này).
 */
export default function OutlinePage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') ?? DEFAULT_TAB

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
        <Empty description="Bạn chưa có đề tài được phân công GVHD">
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

  const trangThai = TRANG_THAI_LABEL[detail.trang_thai] ?? {
    label: detail.trang_thai,
    color: 'default',
  }

  const handleSubmit = async (file: File) => {
    await submitMutation.mutateAsync({ deTaiId, file })
    message.success('Đã nộp phiên bản mới — hệ thống đang kiểm tra trùng lặp')
  }

  return (
    <Card title="Đề cương / Báo cáo cuối">
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{detail.ten_de_tai}</h2>
                  <Tag color={trangThai.color}>{trangThai.label}</Tag>
                </div>
                <Card size="small" title="Nộp phiên bản mới" style={{ marginBottom: 20 }}>
                  <DocumentUpload
                    disabled={!detail.quyen.nop}
                    disabledReason={DISABLED_REASON[detail.trang_thai]}
                    submitLabel="Nộp phiên bản mới"
                    loading={submitMutation.isPending}
                    onSubmit={handleSubmit}
                  />
                </Card>
                <VersionHistory
                  versions={detail.phien_ban}
                  trangThai={detail.trang_thai}
                  docLabel="đề cương"
                />
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
