import { App as AntApp, Button, Empty, List, Space, Tag, Typography } from 'antd'

import { DownloadError, downloadFile } from '../../api/download'
import { formatDate } from '../../utils/format'
import type { MilestoneStatus } from './api'
import { DANH_GIA, TRANG_THAI_MOC, formatDay } from './constants'

const { Text, Paragraph } = Typography

export interface MilestoneListProps {
  moc: MilestoneStatus[]
  selectedId?: number
  onSelect?: (moc: MilestoneStatus) => void
}

/**
 * MH-10 "Các mốc đã nộp": mỗi mốc một dòng "{Mốc} · nộp dd/mm/yyyy" (hoặc
 * "· chưa nộp") + Tag trạng thái (D-05, server tính), nội dung, tệp đính kèm
 * và nhận xét/đánh giá của GVHD. Dùng chung cho SV và GVHD.
 */
export default function MilestoneList({ moc, selectedId, onSelect }: MilestoneListProps) {
  const { message } = AntApp.useApp()

  if (moc.length === 0) {
    return <Empty description="Bộ môn chưa thiết lập mốc tiến độ cho đợt này" />
  }

  const handleDownload = async (id: number, name: string) => {
    try {
      await downloadFile(`/documents/${id}/download`, name)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  return (
    <List
      itemLayout="vertical"
      dataSource={moc}
      renderItem={(item) => {
        const status = TRANG_THAI_MOC[item.trang_thai]
        const report = item.bao_cao
        const selected = item.id === selectedId
        return (
          <List.Item
            key={item.id}
            onClick={onSelect ? () => onSelect(item) : undefined}
            style={{
              cursor: onSelect ? 'pointer' : undefined,
              background: selected ? '#e6f4ff' : undefined,
              borderLeft: selected ? '3px solid #1677ff' : '3px solid transparent',
              paddingLeft: 12,
            }}
          >
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>
                {item.ten_moc} · {report ? `nộp ${formatDate(report.thoi_diem_nop)}` : 'chưa nộp'}
              </Text>
              <Tag color={status.color}>{status.label}</Tag>
            </Space>
            {report ? (
              <div style={{ marginTop: 8 }}>
                <Paragraph style={{ marginBottom: 4, whiteSpace: 'pre-wrap' }}>
                  {report.noi_dung}
                </Paragraph>
                {report.tep && (
                  <Text type="secondary">
                    Tệp đính kèm:{' '}
                    <Button
                      type="link"
                      size="small"
                      style={{ padding: 0 }}
                      onClick={(e) => {
                        e.stopPropagation()
                        if (report.tep) void handleDownload(report.tep.id, report.tep.ten_goc)
                      }}
                    >
                      {report.tep.ten_goc}
                    </Button>
                  </Text>
                )}
                {report.nhan_xet && (
                  <div style={{ marginTop: 8, padding: 8, background: '#fafafa', borderRadius: 6 }}>
                    <Space size={8} style={{ marginBottom: 4 }}>
                      <Text type="secondary">Nhận xét của GVHD</Text>
                      {report.danh_gia && (
                        <Tag color={DANH_GIA[report.danh_gia].color}>
                          {DANH_GIA[report.danh_gia].label}
                        </Tag>
                      )}
                    </Space>
                    <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                      {report.nhan_xet}
                    </Paragraph>
                  </div>
                )}
              </div>
            ) : (
              <Text type="secondary">Hạn nộp {formatDay(item.han_nop)}.</Text>
            )}
          </List.Item>
        )
      }}
    />
  )
}
