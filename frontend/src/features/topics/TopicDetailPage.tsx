import { App as AntApp, Alert, Button, Card, Descriptions, Skeleton, Tag } from 'antd'
import { useNavigate, useParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { TRANG_THAI_DE_TAI } from './constants'
import { useSubmitTopic, useTopic } from './api'

/**
 * MH-06 chế độ chỉ đọc (§3.4.7 "Xem"): chi tiết một đề tài — Đợt đồ án, Lĩnh
 * vực, Người đề xuất, GVHD, Sinh viên, Mô tả, lý do từ chối (nếu có), cùng các
 * hành động Sửa/Gửi đề xuất khi người xem là chủ sở hữu và đề tài còn ở Nháp.
 */
export default function TopicDetailPage() {
  const { id } = useParams()
  const topicId = id !== undefined ? Number(id) : undefined
  const navigate = useNavigate()
  const { message } = AntApp.useApp()

  const { data: topic, isLoading } = useTopic(topicId)
  const submitMutation = useSubmitTopic()

  if (isLoading || !topic) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  const trangThai = TRANG_THAI_DE_TAI[topic.trang_thai] ?? {
    label: topic.trang_thai,
    color: 'default',
  }

  const handleSubmit = async () => {
    if (topicId === undefined) return
    try {
      await submitMutation.mutateAsync(topicId)
      message.success('Đã gửi đề xuất đề tài')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span>{topic.ten_de_tai}</span>
          <Tag color={trangThai.color}>{trangThai.label}</Tag>
        </div>
      }
    >
      {topic.trang_thai === 'TU_CHOI' && (
        <Alert
          type="error"
          showIcon
          message={`Lý do từ chối: ${topic.ly_do_tu_choi ?? ''}`}
          style={{ marginBottom: 16 }}
        />
      )}

      <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
        <Descriptions.Item label="Đợt đồ án">
          {topic.dot_do_an.ten_dot} ({topic.dot_do_an.khoa})
        </Descriptions.Item>
        <Descriptions.Item label="Lĩnh vực">{topic.linh_vuc ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Người đề xuất">
          {topic.nguoi_de_xuat.ho_ten}
          {topic.nguoi_de_xuat.ma ? ` (${topic.nguoi_de_xuat.ma})` : ''}
        </Descriptions.Item>
        <Descriptions.Item label="Giảng viên hướng dẫn">
          {topic.giang_vien_huong_dan
            ? `${topic.giang_vien_huong_dan.ho_ten}${
                topic.giang_vien_huong_dan.ma ? ` (${topic.giang_vien_huong_dan.ma})` : ''
              }`
            : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Sinh viên">
          {topic.sinh_vien
            ? `${topic.sinh_vien.ho_ten}${topic.sinh_vien.ma ? ` (${topic.sinh_vien.ma})` : ''}`
            : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Mô tả">{topic.mo_ta ?? '—'}</Descriptions.Item>
      </Descriptions>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button onClick={() => navigate(-1)}>Quay lại</Button>
        {topic.quyen.sua && (
          <Button onClick={() => navigate(`/de-tai/${topic.id}/sua`)}>Sửa</Button>
        )}
        {topic.quyen.gui && (
          <Button type="primary" loading={submitMutation.isPending} onClick={handleSubmit}>
            Gửi đề xuất
          </Button>
        )}
      </div>
    </Card>
  )
}
