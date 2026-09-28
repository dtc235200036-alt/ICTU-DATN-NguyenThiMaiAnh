import { useMemo, useState } from 'react'
import { Card, Col, Descriptions, Empty, Row, Skeleton, Spin, Tag } from 'antd'
import { AxiosError } from 'axios'
import { useParams } from 'react-router'

import { formatDateTime, formatPercent } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import { useDocumentCheck } from './api'
import type { CheckMatch, CheckSegment } from './api'
import CheckStatusTag from './CheckStatusTag'

const LOAI_LABEL: Record<string, string> = {
  DE_CUONG: 'Đề cương',
  BAO_CAO_TIEN_DO: 'Báo cáo tiến độ',
  BAO_CAO_CUOI: 'Báo cáo cuối',
  KHO: 'Tài liệu lưu kho',
}

// MH-14: 3 mức, mỗi khối luôn có nhãn CHỮ ghi rõ mức + tỷ lệ (không chỉ dựa
// vào màu — đọc được khi in trắng đen hoặc với người khiếm thị màu).
function mucTrungTag(tyLe: number) {
  if (tyLe >= 70) {
    return <Tag color="red">{`Mức trùng: Cao (${tyLe}%)`}</Tag>
  }
  if (tyLe >= 40) {
    return <Tag color="orange">{`Mức trùng: Trung bình (${tyLe}%)`}</Tag>
  }
  return <Tag>{`Mức trùng: Thấp (${tyLe}%)`}</Tag>
}

function SourceRow({
  match,
  active,
  onSelect,
}: {
  match: CheckMatch
  active: boolean
  onSelect: () => void
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect()
      }}
      style={{
        padding: '8px 12px',
        cursor: 'pointer',
        borderRadius: 4,
        background: active ? '#e6f4ff' : undefined,
      }}
    >
      <div style={{ fontSize: 13 }}>{match.doi_tuong_trung}</div>
      <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>{formatPercent(match.ty_le)}</div>
    </div>
  )
}

/**
 * MH-14/UC0.7: skeleton chi tiết kết quả kiểm tra trùng lặp — Phase 4 chỉ
 * thay client (`ai_client.py`), khung màn hình này giữ nguyên. Mở từ
 * CheckPanel ("Xem chi tiết") và từ cột "Kết quả kiểm tra" trong bảng lịch
 * sử phiên bản (Tag "Hoàn tất - N%").
 */
export default function CheckDetailPage() {
  const params = useParams<{ taiLieuId: string }>()
  const taiLieuId = params.taiLieuId !== undefined ? Number(params.taiLieuId) : undefined
  const [selectedSource, setSelectedSource] = useState<string | null>(null)

  const { data, isLoading, isError, error } = useDocumentCheck(taiLieuId)

  const filteredSegments = useMemo<CheckSegment[]>(() => {
    if (!data) return []
    if (selectedSource === null) return data.chi_tiet
    return data.chi_tiet.filter((seg) => seg.doi_tuong_trung === selectedSource)
  }, [data, selectedSource])

  if (isLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  if (isError) {
    const status = error instanceof AxiosError ? error.response?.status : undefined
    if (status === 403) {
      return <ForbiddenPage />
    }
    return (
      <Card>
        <Empty description="Không tìm thấy kết quả kiểm tra" />
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <Empty description="Không tìm thấy kết quả kiểm tra" />
      </Card>
    )
  }

  const loaiLabel = LOAI_LABEL[data.tai_lieu.loai] ?? data.tai_lieu.loai
  const subtitle = `${loaiLabel} v${data.tai_lieu.so_phien_ban} - ${
    data.sinh_vien?.ho_ten ?? '—'
  } - ${data.ten_de_tai}`

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 4px' }}>
        Chi tiết kết quả kiểm tra trùng lặp
      </h1>
      <p style={{ margin: '0 0 20px', fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>{subtitle}</p>

      <Card style={{ marginBottom: 20 }}>
        <Descriptions column={5} size="small">
          <Descriptions.Item label="Tỷ lệ tổng">
            {formatPercent(data.ty_le_tong)}
          </Descriptions.Item>
          <Descriptions.Item label="Ngưỡng áp dụng">
            {formatPercent(data.nguong_ap_dung)}
          </Descriptions.Item>
          <Descriptions.Item label="Trạng thái">
            <CheckStatusTag kiemTra={data} />
          </Descriptions.Item>
          <Descriptions.Item label="Thời điểm kiểm tra">
            {formatDateTime(data.thoi_diem)}
          </Descriptions.Item>
          <Descriptions.Item label="Loại tài liệu">
            {`${loaiLabel} (${data.tai_lieu.dinh_dang})`}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {data.trang_thai === 'DANG_KIEM_TRA' ? (
        <Card>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
              padding: '24px 0',
            }}
          >
            <Spin />
            <p style={{ margin: 0, color: 'rgba(0,0,0,0.45)' }}>Đang kiểm tra, chưa có kết quả.</p>
          </div>
        </Card>
      ) : (
        <Row gutter={20}>
          <Col xs={24} lg={8}>
            <Card size="small" title="Đồ án trùng (lọc đoạn theo nguồn)">
              <div
                role="button"
                tabIndex={0}
                onClick={() => setSelectedSource(null)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') setSelectedSource(null)
                }}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  borderRadius: 4,
                  fontWeight: 500,
                  background: selectedSource === null ? '#e6f4ff' : undefined,
                }}
              >
                Tất cả
              </div>
              {data.do_an_trung.map((match) => (
                <SourceRow
                  key={match.doi_tuong_trung}
                  match={match}
                  active={selectedSource === match.doi_tuong_trung}
                  onSelect={() => setSelectedSource(match.doi_tuong_trung)}
                />
              ))}
            </Card>
          </Col>
          <Col xs={24} lg={16}>
            {filteredSegments.length === 0 ? (
              <Card>
                <Empty description="Không phát hiện đoạn trùng vượt ngưỡng (UC0.7 - A1)" />
              </Card>
            ) : (
              filteredSegments.map((seg, idx) => (
                <Row gutter={16} key={`${seg.doi_tuong_trung}-${idx}`} style={{ marginBottom: 16 }}>
                  <Col xs={24} md={12}>
                    <Card size="small" title="Đoạn trong tài liệu nộp">
                      <div style={{ marginBottom: 8 }}>{mucTrungTag(seg.ty_le)}</div>
                      <p style={{ margin: 0, fontSize: 13 }}>{seg.doan_nguon ?? '—'}</p>
                    </Card>
                  </Col>
                  <Col xs={24} md={12}>
                    <Card size="small" title={`Đoạn nguồn (${seg.doi_tuong_trung})`}>
                      <div style={{ marginBottom: 8 }}>{mucTrungTag(seg.ty_le)}</div>
                      {seg.doan_trung_an ? (
                        <p style={{ margin: 0, fontSize: 13, fontStyle: 'italic', color: 'rgba(0, 0, 0, 0.45)' }}>
                          Nguồn là tài liệu chưa công bố của sinh viên khác — chỉ GVHD và Bộ môn xem được nội
                          dung đoạn này.
                        </p>
                      ) : (
                        <p style={{ margin: 0, fontSize: 13 }}>{seg.doan_trung ?? '—'}</p>
                      )}
                    </Card>
                  </Col>
                </Row>
              ))
            )}
          </Col>
        </Row>
      )}
    </div>
  )
}
