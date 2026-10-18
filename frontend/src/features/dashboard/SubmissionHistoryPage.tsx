import { App as AntApp, Button, Card, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'

import { DownloadError, downloadFile } from '../../api/download'
import { formatDateTime } from '../../utils/format'
import { trangThaiDeCuong } from '../outlines/constants'
import { TRANG_THAI_MOC, formatDay } from '../progress/constants'
import type { TrangThaiMoc } from '../progress/constants'
import { useMySubmissions } from './api'
import type { SubmissionRow } from './api'

function statusColor(row: SubmissionRow): string {
  if (row.loai === 'DE_CUONG') return trangThaiDeCuong(row.trang_thai).color
  if (row.loai === 'TIEN_DO') {
    if (row.thoi_diem_nop === null && row.trang_thai === 'CHUA_DEN_HAN') return 'default'
    return TRANG_THAI_MOC[row.trang_thai as TrangThaiMoc]?.color ?? 'default'
  }
  return row.thoi_diem_nop ? 'success' : 'default'
}

/** SV "Lịch sử nộp": mọi lần nộp (đề cương, báo cáo tiến độ, báo cáo cuối) kèm hạn cuối. */
export default function SubmissionHistoryPage() {
  const { message } = AntApp.useApp()
  const { data, isLoading } = useMySubmissions()

  const columns: ColumnsType<SubmissionRow> = [
    { title: 'STT', key: 'stt', width: 60, render: (_v, _r, idx) => idx + 1 },
    { title: 'Nội dung', dataIndex: 'noi_dung' },
    {
      title: 'Thời gian nộp',
      dataIndex: 'thoi_diem_nop',
      width: 170,
      render: (v: string | null) => formatDateTime(v),
    },
    { title: 'Hạn cuối', dataIndex: 'han_cuoi', width: 120, render: (v: string | null) => formatDay(v) },
    {
      title: 'Trạng thái',
      key: 'trang_thai',
      width: 170,
      render: (_v, r) => <Tag color={statusColor(r)}>{r.trang_thai_label}</Tag>,
    },
    {
      title: 'File',
      key: 'file',
      width: 90,
      render: (_v, r) =>
        r.tai_lieu_id ? (
          <Button
            size="small"
            onClick={() =>
              downloadFile(`/documents/${r.tai_lieu_id}/download`, 'tai-lieu').catch((err: unknown) =>
                message.error(err instanceof DownloadError ? err.message : 'Không tải được file'),
              )
            }
          >
            Tải
          </Button>
        ) : (
          '—'
        ),
    },
  ]

  return (
    <Card title="Lịch sử nộp">
      <Table<SubmissionRow>
        rowKey={(r, idx) => `${r.loai}-${idx}`}
        loading={isLoading}
        columns={columns}
        dataSource={data ?? []}
        pagination={false}
        locale={{ emptyText: 'Bạn chưa có đề tài hoặc chưa nộp tài liệu nào' }}
      />
    </Card>
  )
}
