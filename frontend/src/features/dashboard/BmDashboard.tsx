import { useState } from 'react'
import { Card, List, Select, Skeleton, Statistic } from 'antd'
import { useNavigate } from 'react-router'

import { useCohorts } from '../cohorts/api'
import { useBmDashboard } from './api'

/** MH-04 (subset Phase 2): chỉ số toàn khoa theo đợt + danh sách chờ duyệt mới nhất. */
export default function BmDashboard() {
  const navigate = useNavigate()
  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const { data: cohorts } = useCohorts()
  const { data, isLoading } = useBmDashboard(dotDoAnId)

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
          </div>

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
