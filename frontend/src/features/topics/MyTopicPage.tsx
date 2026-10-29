import { Button, Card, Col, Descriptions, Empty, Row, Skeleton, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router'

import { useCohorts } from '../cohorts/api'
import { useSvDashboard } from '../dashboard/api'
import DinhHuongInfo from '../dinh-huong/DinhHuongInfo'
import { formatDate, formatDateTime } from '../../utils/format'
import { TRANG_THAI_DE_TAI } from './constants'
import { useTopic, useTopicHistory } from './api'
import type { TopicEvent } from './api'

const historyColumns: ColumnsType<TopicEvent> = [
  {
    title: 'Ngày cập nhật',
    dataIndex: 'thoi_diem',
    width: 170,
    render: (v: string) => formatDateTime(v),
  },
  { title: 'Nội dung', dataIndex: 'noi_dung' },
  { title: 'Người thực hiện', dataIndex: 'nguoi_thuc_hien', width: 200 },
]

/** SV "Đề tài của tôi": đề tài hiện tại, thông tin chung và lịch sử đề tài. */
export default function MyTopicPage() {
  const navigate = useNavigate()
  const { data: dashboard, isLoading } = useSvDashboard()
  const topicId = dashboard?.de_tai?.id
  const { data: topic } = useTopic(topicId)
  const { data: history, isLoading: historyLoading } = useTopicHistory(topicId)
  const { data: cohorts } = useCohorts()

  if (isLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }
  if (!dashboard?.de_tai) {
    return (
      <Card title="Đề tài của tôi">
        <Empty
          description={`Bạn chưa được giao đề tài${
            dashboard?.giang_vien_huong_dan ? ` — GVHD: ${dashboard.giang_vien_huong_dan}` : ''
          }. Hãy trao đổi với GVHD; khi được giao, đề tài sẽ hiện ở đây.`}
        />
      </Card>
    )
  }

  const trangThai = TRANG_THAI_DE_TAI[dashboard.de_tai.trang_thai] ?? {
    label: dashboard.de_tai.trang_thai,
    color: 'default',
  }
  const cohort = cohorts?.find((c) => c.id === topic?.dot_do_an.id)

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Đề tài hiện tại" style={{ height: '100%' }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Tên đề tài">{dashboard.de_tai.ten_de_tai}</Descriptions.Item>
              <Descriptions.Item label="GVHD">{dashboard.de_tai.giang_vien_huong_dan ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="Trạng thái">
                <Tag color={trangThai.color}>{trangThai.label}</Tag>
              </Descriptions.Item>
            </Descriptions>
            <Button style={{ marginTop: 12 }} onClick={() => navigate(`/de-tai/${dashboard.de_tai!.id}`)}>
              Xem chi tiết
            </Button>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Thông tin chung" style={{ height: '100%' }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Mã đề tài">DT{String(dashboard.de_tai.id).padStart(4, '0')}</Descriptions.Item>
              <Descriptions.Item label="Lớp">{dashboard.lop ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="Định hướng">
                <DinhHuongInfo value={topic?.dinh_huong} />
              </Descriptions.Item>
              <Descriptions.Item label="Đợt đồ án">{topic?.dot_do_an.ten_dot ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="Ngày giao đề tài">{formatDate(topic?.ngay_giao)}</Descriptions.Item>
              <Descriptions.Item label="Ngày kết thúc dự kiến">{formatDate(cohort?.ngay_ket_thuc)}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
      <Card title="Lịch sử đề tài">
        <Table<TopicEvent>
          rowKey={(r, idx) => `${r.thoi_diem}-${idx}`}
          size="small"
          loading={historyLoading}
          columns={historyColumns}
          dataSource={history ?? []}
          pagination={{ pageSize: 10, hideOnSinglePage: true }}
          locale={{ emptyText: 'Chưa có hoạt động' }}
        />
      </Card>
    </div>
  )
}
