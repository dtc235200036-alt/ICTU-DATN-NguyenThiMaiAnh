import type { ReactNode } from 'react'
import { App as AntApp, Button, Card, Empty, Space, Table, Tag, Timeline } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router'

import { downloadFile, DownloadError } from '../../api/download'
import { formatDate } from '../../utils/format'
import CheckStatusTag from '../documents/CheckStatusTag'
import FilePreviewButton from '../documents/FilePreviewButton'
import type { OutlineTrangThai, OutlineVersion } from './api'

export interface VersionHistoryProps {
  versions: OutlineVersion[]
  trangThai: OutlineTrangThai
  docLabel: 'đề cương' | 'báo cáo cuối'
}

/**
 * MH-08: bảng "Lịch sử phiên bản" + "Nhận xét của GVHD" — dùng chung bởi tab
 * Đề cương (03-02) và tab Báo cáo cuối (03-04, không có vòng lặp sửa-duyệt
 * nên cột Trạng thái duyệt bị ẩn, D-09/§3.4.10).
 */
export default function VersionHistory({ versions, trangThai, docLabel }: VersionHistoryProps) {
  const { message } = AntApp.useApp()
  const navigate = useNavigate()
  const hasReviewLoop = docLabel === 'đề cương'
  const newest = versions[0]

  const handleDownload = async (version: OutlineVersion) => {
    try {
      await downloadFile(`/documents/${version.tai_lieu.id}/download`, version.tai_lieu.ten_goc)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  const columns: ColumnsType<OutlineVersion> = [
    {
      title: 'Phiên bản',
      key: 'phien_ban',
      render: (_value, record) => `v${record.tai_lieu.so_phien_ban}`,
    },
    {
      title: 'Ngày nộp',
      key: 'ngay_nop',
      render: (_value, record) => formatDate(record.tai_lieu.thoi_diem_nop),
    },
    ...(hasReviewLoop
      ? ([
          {
            title: 'Trạng thái duyệt',
            key: 'trang_thai_duyet',
            render: (_value: unknown, record: OutlineVersion) => {
              if (record.luot_duyet) {
                return (
                  <Tag color={record.luot_duyet.ket_qua === 'DA_DUYET' ? 'success' : 'error'}>
                    {record.luot_duyet.ket_qua === 'DA_DUYET' ? 'GVHD đã duyệt' : 'Yêu cầu sửa'}
                  </Tag>
                )
              }
              if (record === newest && trangThai === 'CHO_DUYET') {
                return <Tag color="processing">Chờ GVHD duyệt</Tag>
              }
              return <span style={{ color: 'rgba(0,0,0,0.45)' }}>—</span>
            },
          },
        ] as ColumnsType<OutlineVersion>)
      : []),
    {
      title: 'Kết quả kiểm tra',
      key: 'kiem_tra',
      render: (_value, record) => <CheckStatusTag kiemTra={record.kiem_tra} />,
    },
    {
      title: 'Hành động',
      key: 'hanh_dong',
      render: (_value, record) => (
        <Space>
          <FilePreviewButton doc={record.tai_lieu} />
          <Button size="small" onClick={() => void handleDownload(record)}>
            Tải file
          </Button>
          {record.kiem_tra && (
            <Button
              size="small"
              type="link"
              onClick={() => navigate(`/kiem-tra-trung-lap/${record.tai_lieu.id}`)}
            >
              Xem kết quả
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const timelineItems: { color: string; children: ReactNode }[] = []
  if (hasReviewLoop) {
    for (const version of [...versions].reverse()) {
      if (version.luot_duyet) {
        const isApproved = version.luot_duyet.ket_qua === 'DA_DUYET'
        timelineItems.push({
          color: isApproved ? 'green' : 'red',
          children: (
            <div>
              <p style={{ margin: '0 0 4px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
                {formatDate(version.luot_duyet.thoi_diem)} · v{version.tai_lieu.so_phien_ban} ·{' '}
                {isApproved ? 'GVHD đã duyệt' : 'Yêu cầu sửa'}
              </p>
              <p style={{ margin: 0 }}>
                {version.luot_duyet.nhan_xet
                  ? `${version.luot_duyet.nhan_xet} — ${version.luot_duyet.giang_vien.ho_ten}`
                  : version.luot_duyet.giang_vien.ho_ten}
              </p>
            </div>
          ),
        })
      } else if (version === newest && trangThai === 'CHO_DUYET') {
        timelineItems.push({
          color: 'blue',
          children: (
            <div>
              <p style={{ margin: '0 0 4px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
                {formatDate(version.tai_lieu.thoi_diem_nop)} · v{version.tai_lieu.so_phien_ban} · Đang
                chờ duyệt
              </p>
              <p style={{ margin: 0 }}>Chưa có nhận xét mới (đang chờ GVHD xem xét).</p>
            </div>
          ),
        })
      }
    }
  }

  return (
    <div>
      <Table<OutlineVersion>
        size="small"
        rowKey={(record) => record.tai_lieu.id}
        columns={columns}
        dataSource={versions}
        pagination={false}
        locale={{ emptyText: 'Chưa có phiên bản nào' }}
        style={{ marginBottom: 20 }}
        title={() => <strong>Lịch sử phiên bản</strong>}
      />

      {hasReviewLoop && (
        <Card size="small" title="Nhận xét của GVHD">
          {timelineItems.length > 0 ? (
            <Timeline items={timelineItems} />
          ) : (
            <Empty description="Chưa có nhận xét nào" />
          )}
        </Card>
      )}
    </div>
  )
}
