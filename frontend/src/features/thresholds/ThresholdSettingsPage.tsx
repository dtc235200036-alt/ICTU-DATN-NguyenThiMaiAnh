import { useEffect } from 'react'
import { App as AntApp, Alert, Button, Card, Empty, Form, InputNumber, Popconfirm, Skeleton, Space } from 'antd'
import { AxiosError } from 'axios'

import { getErrorMessage } from '../../api/client'
import { formatDateTime } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import { useSaveThresholds, useThresholds } from './api'
import type { ThresholdOut, ThresholdUpdate } from './api'

// Ngưỡng nguyên văn (MinHash Jaccard) là tham số kỹ thuật của dịch vụ AI, hiệu
// chỉnh ở plan 04-04 (ai-service NGUONG_NGUYEN_VAN_MAC_DINH, calibration/
// nguong-de-xuat.json) — chỉ hiển thị để tham khảo, không sửa từ màn hình này.
const NGUONG_NGUYEN_VAN_KY_THUAT = '88.7%'

function ThresholdExtra({ item }: { item: ThresholdOut }) {
  return (
    <div style={{ marginTop: 4, fontSize: 13, lineHeight: 1.6 }}>
      <div>{item.mo_ta}</div>
      <div>{`Giá trị đề xuất sau hiệu chỉnh: ${item.gia_tri_de_xuat}%`}</div>
      {item.thoi_diem_cap_nhat === null ? (
        <div>Chưa có trong CSDL — lưu cấu hình để ghi giá trị này</div>
      ) : item.nguoi_cap_nhat ? (
        <div>{`Cập nhật lần cuối: ${formatDateTime(item.thoi_diem_cap_nhat)} bởi ${item.nguoi_cap_nhat}`}</div>
      ) : (
        <div>{`Giá trị mặc định từ hiệu chỉnh (cập nhật ${formatDateTime(item.thoi_diem_cap_nhat)})`}</div>
      )}
    </div>
  )
}

/**
 * UC0.4/AISV-07 (D-04): Bộ môn chỉnh ba ngưỡng cảnh báo trùng lặp. Web API gửi
 * ngưỡng hiện hành theo từng request nên thay đổi áp dụng cho lần kiểm tra kế
 * tiếp; kết quả đã ghi giữ ngưỡng lúc kiểm tra (nguong_ap_dung).
 */
export default function ThresholdSettingsPage() {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm<ThresholdUpdate>()
  const { data, isLoading, isError, error } = useThresholds()
  const saveMutation = useSaveThresholds()

  useEffect(() => {
    if (data) {
      form.setFieldsValue(
        Object.fromEntries(data.map((item) => [item.loai, item.gia_tri])) as ThresholdUpdate,
      )
    }
  }, [data, form])

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
        <Alert type="error" showIcon message="Không tải được cấu hình ngưỡng" description={getErrorMessage(error)} />
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <Empty description="Chưa có cấu hình ngưỡng" />
      </Card>
    )
  }

  const handleSave = async () => {
    let values: ThresholdUpdate
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    try {
      await saveMutation.mutateAsync(values)
      message.success('Đã lưu cấu hình ngưỡng')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleRestoreRecommended = () => {
    form.setFieldsValue(
      Object.fromEntries(data.map((item) => [item.loai, item.gia_tri_de_xuat])) as ThresholdUpdate,
    )
  }

  return (
    <Card title="Cấu hình ngưỡng cảnh báo trùng lặp (UC0.4)" style={{ maxWidth: 880 }}>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        message="Ngưỡng mới chỉ áp dụng cho các lần kiểm tra tiếp theo"
        description={`Các kết quả đã kiểm tra trước đó giữ nguyên ngưỡng tại thời điểm kiểm tra. Ngưỡng phát hiện sao chép nguyên văn (MinHash, độ trùng cụm từ ≥ ${NGUONG_NGUYEN_VAN_KY_THUAT}) là tham số kỹ thuật đã hiệu chỉnh của dịch vụ AI và không chỉnh tại đây.`}
      />
      <Form<ThresholdUpdate> form={form} layout="vertical" requiredMark={false}>
        {data.map((item) => (
          <Form.Item
            key={item.loai}
            name={item.loai}
            label={<span style={{ fontWeight: 500 }}>{item.nhan}</span>}
            extra={<ThresholdExtra item={item} />}
            rules={[
              { required: true, message: 'Vui lòng nhập ngưỡng' },
              {
                type: 'number',
                min: 0,
                max: 100,
                message: 'Ngưỡng phải nằm trong khoảng 0–100% (UC0.4 - E1)',
              },
            ]}
          >
            <InputNumber min={0} max={100} step={0.5} precision={2} addonAfter="%" style={{ width: 200 }} />
          </Form.Item>
        ))}
        <Space style={{ marginTop: 8 }}>
          <Button onClick={handleRestoreRecommended}>Khôi phục giá trị đề xuất</Button>
          <Popconfirm
            title="Áp dụng ngưỡng mới cho các lần kiểm tra tiếp theo?"
            okText="Lưu"
            cancelText="Hủy"
            onConfirm={handleSave}
          >
            <Button type="primary" loading={saveMutation.isPending}>
              Lưu cấu hình
            </Button>
          </Popconfirm>
        </Space>
      </Form>
    </Card>
  )
}
