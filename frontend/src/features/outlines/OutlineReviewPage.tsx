import { useEffect, useState } from 'react'
import { App as AntApp, Button, Card, Popconfirm, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useOutline, useOutlines, useReviewOutline } from './api'
import type { OutlineListItem } from './api'

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

/**
 * MH-09 (tracer, thin — fidelity đầy đủ ở plan 03-02): GVHD chọn một đề tài
 * (từ bảng hoặc ?de_tai_id= trên URL), xem tóm tắt nội dung + kết quả kiểm
 * tra trùng lặp của phiên bản mới nhất, và duyệt đề cương.
 */
export default function OutlineReviewPage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialId = searchParams.get('de_tai_id')
  const [selectedId, setSelectedId] = useState<number | undefined>(
    initialId ? Number(initialId) : undefined,
  )

  const { data: outlinesPage, isFetching } = useOutlines({})
  const { data: detail } = useOutline(selectedId)
  const reviewMutation = useReviewOutline()

  useEffect(() => {
    if (selectedId !== undefined) {
      setSearchParams({ de_tai_id: String(selectedId) }, { replace: true })
    }
  }, [selectedId, setSearchParams])

  const latestVersion = detail?.phien_ban[0]

  const handleApprove = async () => {
    if (selectedId === undefined || !latestVersion) return
    try {
      await reviewMutation.mutateAsync({
        deTaiId: selectedId,
        taiLieuDoAnId: latestVersion.tai_lieu.id,
        ketQua: 'DA_DUYET',
      })
      message.success('Đã duyệt đề cương')
    } catch (err) {
      message.error(getErrorMessage(err))
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
        record.phien_ban_moi_nhat ? `v${record.phien_ban_moi_nhat.so_phien_ban}` : '—',
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
      render: (_value, record) =>
        selectedId === record.de_tai_id ? (
          <Button size="small" type="primary" disabled>
            Đang xem
          </Button>
        ) : (
          <Button size="small" onClick={() => setSelectedId(record.de_tai_id)}>
            Xem chi tiết
          </Button>
        ),
    },
  ]

  return (
    <div>
      <Card title="Danh sách đề cương" style={{ marginBottom: 20 }}>
        <Table<OutlineListItem>
          rowKey="de_tai_id"
          loading={isFetching}
          columns={columns}
          dataSource={outlinesPage?.items ?? []}
          locale={{ emptyText: 'Không có đề cương nào' }}
          pagination={false}
        />
      </Card>

      {detail && latestVersion && (
        <Card title={`Duyệt đề cương - ${detail.ten_de_tai}`}>
          <p style={{ marginBottom: 8, fontWeight: 500 }}>Tóm tắt nội dung đã trích xuất</p>
          <p style={{ marginBottom: 16, color: 'rgba(0,0,0,0.65)' }}>
            {latestVersion.tai_lieu.tom_tat ?? '—'}
          </p>

          <Card size="small" title="Kết quả kiểm tra trùng lặp" style={{ marginBottom: 16 }}>
            {!latestVersion.kiem_tra || latestVersion.kiem_tra.trang_thai === 'DANG_KIEM_TRA' ? (
              <p style={{ margin: 0, color: 'rgba(0,0,0,0.45)' }}>
                Đang kiểm tra, chưa có kết quả. GVHD vẫn có thể xem nội dung và duyệt/yêu cầu sửa
                đề cương.
              </p>
            ) : latestVersion.kiem_tra.trang_thai === 'HOAN_TAT' ? (
              <p style={{ margin: 0 }}>
                <strong>{latestVersion.kiem_tra.ty_le_tong ?? 0}%</strong> tỷ lệ tổng · Ngưỡng áp
                dụng của Bộ môn: <strong>{latestVersion.kiem_tra.nguong_ap_dung}%</strong>
              </p>
            ) : (
              <p style={{ margin: 0, color: '#cf1322' }}>Lỗi kiểm tra</p>
            )}
          </Card>

          {detail.quyen.duyet && (
            <Popconfirm title="Duyệt đề cương này?" onConfirm={handleApprove}>
              <Button type="primary" loading={reviewMutation.isPending}>
                Duyệt đề cương
              </Button>
            </Popconfirm>
          )}
        </Card>
      )}
    </div>
  )
}
