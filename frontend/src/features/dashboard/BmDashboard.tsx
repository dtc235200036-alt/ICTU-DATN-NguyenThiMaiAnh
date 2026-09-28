import { useState } from 'react'
import { Button, Card, Col, List, Row, Select, Skeleton, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router'

import { useCohorts } from '../cohorts/api'
import type { MilestoneOut, ProgressRow } from '../progress/api'
import { TRANG_THAI_MOC, formatDay } from '../progress/constants'
import { useBmDashboard } from './api'

/** MH-04: chỉ số toàn khoa theo đợt (đề tài, SV trễ mốc, hội đồng sắp tới),
 * trích tiến độ 5 SV, mốc của đợt và danh sách đề tài chờ duyệt mới nhất. */
export default function BmDashboard() {
  const navigate = useNavigate()
  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const { data: cohorts } = useCohorts()
  const { data, isLoading } = useBmDashboard(dotDoAnId)

  const progressLink = (extra = '') => {
    const dot = data?.dot_do_an?.id
    const params = [dot ? `dot_do_an_id=${dot}` : '', extra].filter(Boolean).join('&')
    return `/tien-do-toan-khoa${params ? `?${params}` : ''}`
  }

  const moc = data?.tien_do_trich?.moc ?? []
  const progressColumns: ColumnsType<ProgressRow> = [
    {
      title: 'Sinh viên',
      key: 'sinh_vien',
      render: (_v, r) =>
        r.sinh_vien ? `${r.sinh_vien.ho_ten}${r.sinh_vien.ma ? ` (${r.sinh_vien.ma})` : ''}` : '—',
    },
    { title: 'Đề tài', key: 'de_tai', render: (_v, r) => r.de_tai.ten_de_tai },
    ...moc.map((m) => ({
      title: m.ten_moc,
      key: `moc-${m.id}`,
      render: (_v: unknown, r: ProgressRow) => {
        const cell = r.o.find((c) => c.moc_id === m.id)
        if (!cell) return '—'
        const s = TRANG_THAI_MOC[cell.trang_thai]
        return <Tag color={s.color}>{s.label}</Tag>
      },
    })),
  ]
  const milestoneColumns: ColumnsType<MilestoneOut> = [
    { title: 'Mốc', dataIndex: 'ten_moc' },
    { title: 'Hạn nộp', dataIndex: 'han_nop', render: (v: string | null) => formatDay(v) },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 20 }}>
        <Select
          allowClear
          placeholder={
            data?.dot_do_an ? `${data.dot_do_an.ten_dot} (${data.dot_do_an.khoa})` : 'Chọn đợt đồ án'
          }
          style={{ width: 280 }}
          value={dotDoAnId}
          onChange={(value: number | undefined) => setDotDoAnId(value)}
          options={(cohorts ?? []).map((c) => ({ value: c.id, label: `${c.ten_dot} (${c.khoa})` }))}
        />
      </div>

      {isLoading || !data ? (
        <Card>
          <Skeleton active />
        </Card>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
            <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/duyet-de-tai')}>
              <Statistic
                title="Đề tài chờ duyệt"
                value={data.de_tai_cho_duyet}
                valueStyle={data.de_tai_cho_duyet > 0 ? { color: '#cf1322' } : undefined}
              />
            </Card>
            <Card style={{ minWidth: 220 }}>
              <Statistic
                title="SV chưa có đề tài"
                value={data.sv_chua_co_de_tai}
                suffix={`/ ${data.tong_sinh_vien}`}
              />
            </Card>
            <Card style={{ minWidth: 220 }}>
              <Statistic title="Đề tài đã phân công" value={data.de_tai_da_phan_cong} />
            </Card>
            <Card
              style={{ minWidth: 220, cursor: 'pointer' }}
              onClick={() => navigate(progressLink('chi_tre_moc=1'))}
            >
              <Statistic
                title="SV trễ mốc"
                value={data.sv_tre_moc}
                valueStyle={data.sv_tre_moc > 0 ? { color: '#cf1322' } : undefined}
              />
            </Card>
            <Card style={{ minWidth: 220, cursor: 'pointer' }} onClick={() => navigate('/hoi-dong')}>
              <Statistic title="Hội đồng sắp tới" value={data.so_hoi_dong_sap_toi} />
            </Card>
          </div>

          <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
            <Col xs={24} xl={16}>
              <Card
                title={`Tiến độ Sinh viên (trích ${data.tien_do_trich?.items.length ?? 0}/${data.tien_do_trich?.tong ?? 0})`}
                extra={<a onClick={() => navigate(progressLink())}>Xem tất cả</a>}
              >
                <Table<ProgressRow>
                  rowKey={(r) => r.de_tai.id}
                  columns={progressColumns}
                  dataSource={data.tien_do_trich?.items ?? []}
                  pagination={false}
                  size="small"
                  scroll={{ x: true }}
                  locale={{ emptyText: 'Chưa có sinh viên được phân công trong đợt này' }}
                />
              </Card>
            </Col>
            <Col xs={24} xl={8}>
              <Card
                title="Mốc tiến độ của đợt"
                extra={
                  <Button size="small" type="primary" onClick={() => navigate(progressLink())}>
                    Thiết lập mốc
                  </Button>
                }
              >
                <Table<MilestoneOut>
                  rowKey="id"
                  columns={milestoneColumns}
                  dataSource={data.moc_tien_do}
                  pagination={false}
                  size="small"
                  locale={{ emptyText: 'Chưa thiết lập mốc' }}
                />
              </Card>
            </Col>
          </Row>

          <Card
            title="Đề tài chờ duyệt mới nhất"
            extra={<a onClick={() => navigate('/duyet-de-tai')}>Xem tất cả</a>}
          >
            <List
              locale={{ emptyText: 'Không có đề tài chờ duyệt' }}
              dataSource={data.cho_duyet_moi_nhat}
              renderItem={(item) => (
                <List.Item>
                  <span>{item.ten_de_tai}</span>
                  <span style={{ color: 'rgba(0,0,0,0.45)' }}>{item.nguoi_de_xuat}</span>
                </List.Item>
              )}
            />
          </Card>
        </>
      )}
    </div>
  )
}
