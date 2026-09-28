import { App as AntApp, Card, Col, Row, Skeleton } from 'antd'

import { useFinalReport, useSubmitFinalReport } from '../defense/api'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import CheckPanel from '../documents/CheckPanel'
import DocumentUpload from '../documents/DocumentUpload'
import VersionHistory from './VersionHistory'

export interface FinalReportTabProps {
  deTaiId: number
}

/**
 * MH-08 (SV) — tab "Báo cáo cuối" (UC4.1): không có vòng lặp yêu cầu sửa như
 * đề cương (`VersionHistory` với `docLabel='báo cáo cuối'` tự ẩn cột Trạng
 * thái duyệt + Card nhận xét GVHD); Bộ môn vẫn lập được hội đồng trong lúc
 * kiểm tra còn Đang kiểm tra (UC4.1 - E2).
 */
export default function FinalReportTab({ deTaiId }: FinalReportTabProps) {
  const { message } = AntApp.useApp()
  const { data: detail, isLoading, isError, error, refetch } = useFinalReport(deTaiId)
  const submitMutation = useSubmitFinalReport()

  if (isError) {
    return (
      <Card>
        <QueryErrorAlert error={error} onRetry={() => void refetch()} />
      </Card>
    )
  }

  if (isLoading || !detail) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  const disabledReason = detail.da_xep_lich
    ? 'Bạn đã được xếp lịch bảo vệ — không thể nộp lại báo cáo cuối.'
    : !detail.quyen.nop
      ? 'Cần có đề cương đã được duyệt trước khi nộp báo cáo cuối (UC4.1).'
      : undefined

  const handleSubmit = async (file: File) => {
    await submitMutation.mutateAsync({ deTaiId, file })
    message.success('Đã nộp báo cáo cuối — hệ thống đang kiểm tra trùng lặp')
  }

  const newest = detail.phien_ban[0]
  const versionsForHistory = detail.phien_ban.map((version) => ({
    tai_lieu: version.tai_lieu,
    kiem_tra: version.kiem_tra,
    luot_duyet: null,
  }))

  return (
    <div>
      <Card size="small" title="Nộp báo cáo cuối" style={{ marginBottom: 20 }}>
        <DocumentUpload
          disabled={!detail.quyen.nop}
          disabledReason={disabledReason}
          submitLabel="Nộp báo cáo cuối"
          loading={submitMutation.isPending}
          onSubmit={handleSubmit}
        />
      </Card>

      <Row gutter={20}>
        <Col xs={24} lg={14}>
          <VersionHistory
            versions={versionsForHistory}
            trangThai="DA_DUYET"
            docLabel="báo cáo cuối"
          />
        </Col>
        <Col xs={24} lg={10}>
          <CheckPanel
            taiLieuId={newest?.tai_lieu.id}
            canRecheck={false}
            pendingText="Đang kiểm tra, chưa có kết quả. Bộ môn vẫn có thể lập hội đồng (UC4.1 - E2)."
          />
        </Col>
      </Row>
    </div>
  )
}
