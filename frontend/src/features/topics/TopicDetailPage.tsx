import { App as AntApp, Alert, Button, Card, Descriptions, Result, Skeleton, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { useNavigate, useParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import ForbiddenPage from '../auth/ForbiddenPage'
import { TRANG_THAI_DE_TAI } from './constants'
import { useSubmitTopic, useTopic } from './api'
import type { SavedChiTietTrungLap } from './api'

const chiTietColumns: ColumnsType<SavedChiTietTrungLap> = [
  { title: 'Đề tài tương tự', dataIndex: 'doi_tuong_trung' },
  { title: 'Tỷ lệ', dataIndex: 'ty_le', render: (ty_le: number) => `${ty_le}%` },
]

function formatThoiDiem(iso: string): string {
  return new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(iso))
}

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

  const { data: topic, isLoading, isError, error } = useTopic(topicId)
  const submitMutation = useSubmitTopic()

  if (isError) {
    // T-02-23: server trả 403 khi người xem không phải chủ sở hữu/Bộ môn và đề
    // tài chưa đủ điều kiện xem công khai — không được kẹt ở Skeleton mãi mãi.
    const status = error instanceof AxiosError ? error.response?.status : undefined
    if (status === 403) {
      return <ForbiddenPage />
    }
    return (
      <Card>
        <Result status="error" title="Không tải được đề tài" subTitle={getErrorMessage(error)} />
      </Card>
    )
  }

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

      {topic.kiem_tra_ten && (
        <Card size="small" title="Kết quả kiểm tra trùng tên (UC0.6)" style={{ marginBottom: 16 }}>
          {topic.kiem_tra_ten.trang_thai === 'LOI' ? (
            <Tag>Chưa kiểm tra</Tag>
          ) : topic.kiem_tra_ten.chi_tiet.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Tag color="success">Không trùng</Tag>
              <span>Ngưỡng áp dụng: {topic.kiem_tra_ten.nguong_ap_dung}%</span>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
                <Tag color="warning">{topic.kiem_tra_ten.chi_tiet.length} đề tài tương tự</Tag>
                <span>Ngưỡng áp dụng: {topic.kiem_tra_ten.nguong_ap_dung}%</span>
              </div>
              <Table<SavedChiTietTrungLap>
                size="small"
                rowKey="doi_tuong_trung"
                pagination={false}
                columns={chiTietColumns}
                dataSource={topic.kiem_tra_ten.chi_tiet}
              />
            </div>
          )}
          <div style={{ marginTop: 8, color: 'rgba(0,0,0,0.45)', fontSize: 12 }}>
            Thời điểm kiểm tra: {formatThoiDiem(topic.kiem_tra_ten.thoi_diem)}
          </div>
        </Card>
      )}

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
