import { useEffect, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  List,
  Radio,
  Row,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useProgressStudents, useReviewReport, useTopicProgress } from './api'
import type { MilestoneStatus } from './api'
import type { DanhGia } from './constants'
import { DANH_GIA_OPTIONS, TRANG_THAI_MOC, formatDay } from './constants'
import MilestoneList from './MilestoneList'

const { TextArea } = Input
const { Text } = Typography

/**
 * MH-10 (phía GVHD)/UC3.3: trái — SV mình hướng dẫn (Badge số báo cáo chờ
 * nhận xét, Tag "Trễ mốc"); phải — các mốc của SV đã chọn (?de_tai_id=) và
 * form "Nhận xét cho {mốc}" cho báo cáo đã nộp. Mốc quá hạn chưa nộp chỉ
 * hiện Tag "Trễ mốc" (UC3.3 E1 qua cờ tính sẵn, không ghi dòng nào).
 */
export default function ProgressReviewPage() {
  const { message } = AntApp.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const deTaiParam = searchParams.get('de_tai_id')
  const deTaiId = deTaiParam ? Number(deTaiParam) : undefined

  const { data: students, isLoading: studentsLoading } = useProgressStudents()
  const { data: topic, isError, error, isFetching } = useTopicProgress(deTaiId)
  const reviewMutation = useReviewReport()

  const [mocId, setMocId] = useState<number | undefined>(undefined)
  const [nhanXet, setNhanXet] = useState('')
  const [danhGia, setDanhGia] = useState<DanhGia>('DAT')

  const selected: MilestoneStatus | undefined = topic?.moc.find((m) => m.id === mocId)

  // Mặc định chọn báo cáo đầu tiên đang chờ nhận xét.
  useEffect(() => {
    if (!topic) return
    if (mocId !== undefined && topic.moc.some((m) => m.id === mocId)) return
    const pending = topic.moc.find((m) => m.bao_cao && m.bao_cao.nhan_xet === null)
    setMocId(pending?.id ?? topic.moc.find((m) => m.bao_cao)?.id)
  }, [topic, mocId])

  useEffect(() => {
    setNhanXet(selected?.bao_cao?.nhan_xet ?? '')
    setDanhGia(selected?.bao_cao?.danh_gia ?? 'DAT')
  }, [selected?.id, selected?.bao_cao?.id, selected?.bao_cao?.nhan_xet])

  const openStudent = (id: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('de_tai_id', String(id))
    setSearchParams(next, { replace: true })
    setMocId(undefined)
  }

  const handleReview = async () => {
    if (!selected?.bao_cao) return
    if (nhanXet.trim().length === 0) {
      message.error('Vui lòng nhập nhận xét')
      return
    }
    try {
      await reviewMutation.mutateAsync({
        baoCaoId: selected.bao_cao.id,
        nhanXet: nhanXet.trim(),
        danhGia,
      })
      message.success(`Đã gửi nhận xét cho ${selected.ten_moc}`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const renderReviewCard = () => {
    if (!topic || !selected) return null
    if (!selected.bao_cao) {
      return (
        <Card title={`Nhận xét cho ${selected.ten_moc}`} style={{ marginTop: 16 }}>
          <Space>
            <Tag color={TRANG_THAI_MOC[selected.trang_thai].color}>
              {TRANG_THAI_MOC[selected.trang_thai].label}
            </Tag>
            <Text type="secondary">
              Sinh viên chưa nộp báo cáo mốc này (hạn {formatDay(selected.han_nop)}).
            </Text>
          </Space>
        </Card>
      )
    }
    return (
      <Card title={`Nhận xét cho ${selected.ten_moc}`} style={{ marginTop: 16 }}>
        {selected.trang_thai === 'NOP_TRE' && selected.so_ngay_tre !== null && (
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
            message={`Nộp trễ ${selected.so_ngay_tre} ngày so với hạn ${formatDay(selected.han_nop)}.`}
          />
        )}
        <Form layout="vertical" disabled={!topic.co_the_nhan_xet}>
          <Form.Item label="Nhận xét" required>
            <TextArea
              rows={4}
              maxLength={5000}
              value={nhanXet}
              onChange={(e) => setNhanXet(e.target.value)}
            />
          </Form.Item>
          <Form.Item label="Đánh giá">
            <Radio.Group
              value={danhGia}
              onChange={(e) => setDanhGia(e.target.value as DanhGia)}
              options={DANH_GIA_OPTIONS}
            />
          </Form.Item>
          <Button type="primary" loading={reviewMutation.isPending} onClick={handleReview}>
            Gửi nhận xét
          </Button>
        </Form>
      </Card>
    )
  }

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={8}>
        <Card title="Sinh viên hướng dẫn">
          {studentsLoading ? (
            <Spin />
          ) : (
            <List
              dataSource={students ?? []}
              locale={{ emptyText: 'Chưa có sinh viên được phân công' }}
              renderItem={(item) => (
                <List.Item
                  onClick={() => openStudent(item.de_tai_id)}
                  style={{
                    cursor: 'pointer',
                    background: item.de_tai_id === deTaiId ? '#e6f4ff' : undefined,
                    paddingLeft: 8,
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <span>
                          {item.sinh_vien
                            ? `${item.sinh_vien.ho_ten}${item.sinh_vien.ma ? ` (${item.sinh_vien.ma})` : ''}`
                            : '—'}
                        </span>
                        {item.tre_moc && <Tag color="red">Trễ mốc</Tag>}
                      </Space>
                    }
                    description={item.ten_de_tai}
                  />
                  <Badge count={item.so_cho_nhan_xet} title="Báo cáo chờ nhận xét" />
                </List.Item>
              )}
            />
          )}
        </Card>
      </Col>
      <Col xs={24} lg={16}>
        {deTaiId === undefined ? (
          <Card>
            <Empty description="Chọn một sinh viên để xem báo cáo tiến độ" />
          </Card>
        ) : isError ? (
          <Alert type="error" showIcon message={getErrorMessage(error)} />
        ) : !topic ? (
          <Spin spinning={isFetching} />
        ) : (
          <>
            <Card
              title={`Báo cáo tiến độ - ${topic.sinh_vien?.ho_ten ?? ''}`}
              extra={<Text type="secondary">{topic.ten_de_tai}</Text>}
            >
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                Các mốc đã nộp
              </Text>
              <MilestoneList moc={topic.moc} selectedId={mocId} onSelect={(m) => setMocId(m.id)} />
            </Card>
            {renderReviewCard()}
          </>
        )}
      </Col>
    </Row>
  )
}
