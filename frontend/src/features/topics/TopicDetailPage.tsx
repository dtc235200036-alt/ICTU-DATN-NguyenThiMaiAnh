import {
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Input,
  Modal,
  Result,
  Skeleton,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { DownloadError, downloadFile } from '../../api/download'
import { formatBytes, formatDate } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import DinhHuongInfo from '../dinh-huong/DinhHuongInfo'
import { TRANG_THAI_DE_TAI } from './constants'
import { useSubmitTopic, useTopic, useWithdrawTopic } from './api'
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
 * MH-07 "Chi tiết đề tài được giao" (§3.4.7 "Xem", UC1.2): Đợt đồ án, Định hướng,
 * GVHD, Sinh viên, Mô tả, kết quả kiểm tra trùng tên đã lưu (UC0.6), cùng các
 * hành động Sửa / Giao đề tài cho sinh viên khi người xem là GVHD sở hữu và đề
 * tài còn ở Nháp; Thu hồi đề tài (về Nháp) khi đề tài đã giao.
 */
export default function TopicDetailPage() {
  const { id } = useParams()
  const topicId = id !== undefined ? Number(id) : undefined
  const navigate = useNavigate()
  const { message } = AntApp.useApp()

  const { data: topic, isLoading, isError, error } = useTopic(topicId)
  const submitMutation = useSubmitTopic()
  const withdrawMutation = useWithdrawTopic()
  const [moThuHoi, setMoThuHoi] = useState(false)
  const [lyDo, setLyDo] = useState('')

  if (isError) {
    // T-02-23/UC0.8: server trả 403 khi người xem không phải GVHD, Bộ môn hay
    // SV được giao đề tài — không được kẹt ở Skeleton mãi mãi.
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
      message.success('Đã giao đề tài cho sinh viên')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleWithdraw = async () => {
    if (topicId === undefined) return
    try {
      await withdrawMutation.mutateAsync({ id: topicId, ly_do: lyDo.trim() || null })
      message.success('Đã thu hồi đề tài — đề tài trở về Nháp')
      setMoThuHoi(false)
      setLyDo('')
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
      <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
        <Descriptions.Item label="Đợt đồ án">
          {topic.dot_do_an.ten_dot} ({topic.dot_do_an.khoa})
        </Descriptions.Item>
        <Descriptions.Item label="Định hướng">
          <DinhHuongInfo value={topic.dinh_huong} />
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
        <Descriptions.Item label="Ngày giao">{formatDate(topic.ngay_giao)}</Descriptions.Item>
        <Descriptions.Item label="Mô tả">{topic.mo_ta ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="File đính kèm">
          {topic.tep_dinh_kem ? (
            <Button
              type="link"
              style={{ padding: 0 }}
              onClick={() => {
                const tep = topic.tep_dinh_kem!
                downloadFile(`/documents/${tep.id}/download`, tep.ten_goc).catch((err: unknown) =>
                  message.error(err instanceof DownloadError ? err.message : 'Không tải được file'),
                )
              }}
            >
              ⬇ {topic.tep_dinh_kem.ten_goc} ({formatBytes(topic.tep_dinh_kem.kich_thuoc)})
            </Button>
          ) : (
            '—'
          )}
        </Descriptions.Item>
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
            Giao đề tài cho sinh viên
          </Button>
        )}
        {topic.quyen.thu_hoi && (
          <Button danger onClick={() => setMoThuHoi(true)}>
            Thu hồi đề tài
          </Button>
        )}
      </div>

      <Modal
        title="Thu hồi đề tài"
        open={moThuHoi}
        okText="Thu hồi"
        cancelText="Hủy"
        okButtonProps={{ danger: true }}
        confirmLoading={withdrawMutation.isPending}
        onOk={handleWithdraw}
        onCancel={() => setMoThuHoi(false)}
      >
        <p>
          Đề tài trở về <b>Nháp</b>
          {topic.sinh_vien ? ` và sinh viên ${topic.sinh_vien.ho_ten}` : ''} không còn thấy đề tài này.
          Sau đó GVHD sửa rồi giao lại, hoặc giao đề tài khác cho sinh viên. Không thu hồi được khi
          sinh viên đã nộp đề cương hoặc báo cáo tiến độ.
        </p>
        <Input.TextArea
          rows={3}
          maxLength={500}
          showCount
          style={{ marginBottom: 24 }}
          placeholder="Lý do (không bắt buộc) — gửi kèm thông báo cho sinh viên"
          value={lyDo}
          onChange={(e) => setLyDo(e.target.value)}
        />
      </Modal>
    </Card>
  )
}
