import { useMemo, useState } from 'react'
import { Alert, Card, Col, Descriptions, Empty, Row, Skeleton, Space, Spin, Tag, theme } from 'antd'
import { AxiosError } from 'axios'
import { useParams } from 'react-router'

import { formatDateTime, formatPercent } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import { useDocumentCheck } from './api'
import type { CheckMatch, CheckSegment } from './api'
import { scopeText } from './scope'
import { thresholdText, warningReason } from './warning'
import CheckStatusTag from './CheckStatusTag'
import { highlightOverlap, parseViTri } from './highlight'

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

// 04-06: tín hiệu kích hoạt lưu trong vi_tri — giải thích VÌ SAO đoạn bị gắn cờ
// (nguyên văn: vân tay cụm âm tiết; ngữ nghĩa: embedding — có thể ít từ trùng).
function tinHieuTag(tinHieu: 'NGUYEN_VAN' | 'NGU_NGHIA' | null) {
  if (tinHieu === 'NGUYEN_VAN') return <Tag color="red">Trùng nguyên văn</Tag>
  if (tinHieu === 'NGU_NGHIA') return <Tag color="orange">Trùng ngữ nghĩa</Tag>
  return null
}

/**
 * AISV-05/T-04-31: đoạn văn với các cụm từ dùng chung bọc trong <mark> — chỉ
 * React text node, không bao giờ chèn HTML thô từ nội dung trích xuất.
 */
function HighlightedText({ text, other, markBg }: { text: string; other: string; markBg: string }) {
  const segments = useMemo(() => highlightOverlap(text, other), [text, other])
  return (
    <p style={{ margin: 0, fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
      {segments.map((segment, i) =>
        segment.match ? (
          <mark key={i} style={{ background: markBg, padding: '0 1px', borderRadius: 2, color: 'inherit' }}>
            {segment.text}
          </mark>
        ) : (
          <span key={i}>{segment.text}</span>
        ),
      )}
    </p>
  )
}

const COLUMN_LABEL_STYLE = {
  margin: '0 0 6px',
  fontSize: 12,
  fontWeight: 500,
  color: 'rgba(0,0,0,0.45)',
} as const

function SegmentCard({ seg, markBg }: { seg: CheckSegment; markBg: string }) {
  const { viTri, tinHieu } = parseViTri(seg.vi_tri)
  const nguon = seg.doan_nguon ?? ''
  const trung = seg.doan_trung ?? ''
  return (
    <Card
      size="small"
      style={{ marginBottom: 16 }}
      title={
        <Space size={8} wrap>
          <span style={{ fontWeight: 500 }}>{viTri || 'Đoạn trùng'}</span>
          {mucTrungTag(seg.ty_le)}
          {tinHieuTag(tinHieu)}
        </Space>
      }
    >
      <Row gutter={24}>
        <Col xs={24} md={12}>
          <p style={COLUMN_LABEL_STYLE}>Đoạn trong tài liệu nộp</p>
          {nguon ? <HighlightedText text={nguon} other={trung} markBg={markBg} /> : <p style={{ margin: 0 }}>—</p>}
        </Col>
        <Col xs={24} md={12}>
          <p style={COLUMN_LABEL_STYLE}>{`Đoạn nguồn (${seg.doi_tuong_trung})`}</p>
          {seg.doan_trung_an ? (
            <p style={{ margin: 0, fontSize: 13, fontStyle: 'italic', color: 'rgba(0, 0, 0, 0.45)' }}>
              Nguồn là tài liệu chưa công bố của sinh viên khác — chỉ GVHD và Bộ môn xem được nội dung đoạn
              này.
            </p>
          ) : trung ? (
            <HighlightedText text={trung} other={nguon} markBg={markBg} />
          ) : (
            <p style={{ margin: 0 }}>—</p>
          )}
        </Col>
      </Row>
    </Card>
  )
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
 * MH-14/UC0.7/AISV-05: chi tiết kết quả kiểm tra trùng lặp — mỗi đoạn trùng
 * đặt cạnh đoạn nguồn, cụm từ dùng chung được tô (highlightOverlap), nhãn tín
 * hiệu "Trùng nguyên văn"/"Trùng ngữ nghĩa" giải thích lý do (04-07). Mở từ
 * CheckPanel ("Xem chi tiết") và từ cột "Kết quả kiểm tra" trong bảng lịch
 * sử phiên bản (Tag "Hoàn tất - N%").
 */
export default function CheckDetailPage() {
  const params = useParams<{ taiLieuId: string }>()
  const taiLieuId = params.taiLieuId !== undefined ? Number(params.taiLieuId) : undefined
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const { token } = theme.useToken()

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
        <Descriptions column={3} size="small">
          <Descriptions.Item label="Tỷ lệ tổng">
            {formatPercent(data.ty_le_tong)}
          </Descriptions.Item>
          <Descriptions.Item label="Trùng nhiều nhất với một đồ án">
            {formatPercent(data.ty_le_nguon_cao_nhat)}
          </Descriptions.Item>
          <Descriptions.Item label="Ngưỡng áp dụng">
            {thresholdText(data)}
            {data.vuot_nguong !== null ? (
              <Tag
                color={data.vuot_nguong ? 'error' : 'success'}
                style={{ marginLeft: 8 }}
                title={warningReason(data) ?? undefined}
              >
                {data.ly_do_vuot_nguong === 'TONG_NGUON'
                  ? 'Vượt ngưỡng tổng nhiều đồ án'
                  : data.vuot_nguong
                    ? 'Vượt ngưỡng cảnh báo'
                    : 'Dưới ngưỡng cảnh báo'}
              </Tag>
            ) : null}
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
            {data.trang_thai === 'HOAN_TAT' ? (
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                message={`Đã loại trừ phần mẫu chung: tiêu đề mẫu, mục lục, tài liệu tham khảo trước khi so sánh (FR-AI-02).${
                  scopeText(data) ? ` ${scopeText(data)}.` : ''
                }`}
                description="Phần tô màu là cụm từ (từ 3 từ liên tiếp) xuất hiện ở cả hai đoạn. Đoạn trùng ngữ nghĩa có thể ít từ chung — nhãn cho biết lý do đoạn bị đánh dấu."
              />
            ) : null}
            {data.trang_thai === 'HOAN_TAT' && data.loai_tru_nhieu ? (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                message={`${formatPercent(data.ty_le_loai_tru)} nội dung bị loại như phần mẫu chung và không được kiểm tra`}
                description="Hãy mở trực tiếp tài liệu để xem các mục bị loại (phụ lục, mục lục, tài liệu tham khảo…) có thực sự là phần mẫu chung không."
              />
            ) : null}
            {filteredSegments.length === 0 ? (
              <Card>
                <Empty description="Không phát hiện đoạn trùng vượt ngưỡng (UC0.7 - A1)" />
              </Card>
            ) : (
              filteredSegments.map((seg, idx) => (
                <SegmentCard key={`${seg.doi_tuong_trung}-${seg.vi_tri ?? ''}-${idx}`} seg={seg} markBg={token.colorWarningBgHover} />
              ))
            )}
          </Col>
        </Row>
      )}
    </div>
  )
}
