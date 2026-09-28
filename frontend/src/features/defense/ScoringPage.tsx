import { useEffect } from 'react'
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Row,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { Link, useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { downloadFile, DownloadError } from '../../api/download'
import { formatBytes, formatDate, formatPercent } from '../../utils/format'
import QueryErrorAlert from '../../components/QueryErrorAlert'
import ForbiddenPage from '../auth/ForbiddenPage'
import CheckStatusTag from '../documents/CheckStatusTag'
import RecheckButton from '../documents/RecheckButton'
import { useMyCommittees, useScheduleForScoring, useScore } from './api'
import type { MyCommittee, MyCommitteeRow, ScoringDetail } from './api'

const { Text } = Typography

interface ScoreFormValues {
  diem: number | null
  nhan_xet: string
}

function committeeLabel(item: Pick<MyCommittee, 'ten_hoi_dong' | 'ngay_bao_ve' | 'phong'>): string {
  return `${item.ten_hoi_dong} - ${formatDate(item.ngay_bao_ve)} - Phòng ${item.phong}`
}

function CheckSummaryBlock({ detail }: { detail: ScoringDetail }) {
  const kiemTra = detail.kiem_tra
  if (kiemTra && kiemTra.trang_thai === 'HOAN_TAT' && detail.bao_cao_cuoi) {
    // CR-01: vượt ngưỡng = tỷ lệ trùng với một đồ án nguồn >= ngưỡng (Web API tính).
    const over = kiemTra.vuot_nguong === true
    return (
      <div>
        <Text>
          {`Tỷ lệ tổng ${formatPercent(kiemTra.ty_le_tong)}; trùng nhiều nhất với một đồ án ${formatPercent(
            kiemTra.ty_le_nguon_cao_nhat,
          )} - ${over ? 'vượt' : 'dưới'} ngưỡng ${formatPercent(kiemTra.nguong_ap_dung)} của Bộ môn.`}
        </Text>{' '}
        <Link to={`/kiem-tra-trung-lap/${detail.bao_cao_cuoi.id}`}>Xem chi tiết</Link>
      </div>
    )
  }
  if (
    kiemTra &&
    kiemTra.trang_thai === 'LOI' &&
    detail.bao_cao_cuoi &&
    !detail.bao_cao_cuoi.trich_xuat_loi
  ) {
    return (
      <Space size={6} wrap>
        <CheckStatusTag kiemTra={kiemTra} />
        <RecheckButton taiLieuId={detail.bao_cao_cuoi.id} />
      </Space>
    )
  }
  return <CheckStatusTag kiemTra={kiemTra} />
}

function ScoringPanel({ lichId }: { lichId: number }) {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm<ScoreFormValues>()
  const { data: detail, isLoading, isError, error } = useScheduleForScoring(lichId)
  const scoreMutation = useScore()

  useEffect(() => {
    form.setFieldsValue({
      diem: detail?.diem_cua_toi?.diem ?? null,
      nhan_xet: detail?.diem_cua_toi?.nhan_xet ?? '',
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail?.id, detail?.diem_cua_toi?.diem, detail?.diem_cua_toi?.nhan_xet])

  if (isLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }
  if (isError || !detail) {
    const status = error instanceof AxiosError ? error.response?.status : undefined
    if (status === 403) return <ForbiddenPage />
    return (
      <Card>
        <Alert type="error" showIcon message={getErrorMessage(error)} />
      </Card>
    )
  }

  const handleDownload = async () => {
    if (!detail.bao_cao_cuoi) return
    try {
      await downloadFile(`/documents/${detail.bao_cao_cuoi.id}/download`, detail.bao_cao_cuoi.ten_goc)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  const handleSave = async () => {
    let values: ScoreFormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    try {
      await scoreMutation.mutateAsync({
        lichId,
        input: { diem: values.diem as number, nhan_xet: values.nhan_xet?.trim() || null },
      })
      message.success('Đã lưu điểm')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  return (
    <Card title={`Chấm điểm - ${detail.sinh_vien.ho_ten}`}>
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <div>
          <div style={{ fontWeight: 500 }}>{detail.ten_de_tai}</div>
          <Text type="secondary">
            {`${detail.sinh_vien.ma ?? ''} · ${detail.ten_hoi_dong} · ${formatDate(detail.ngay_bao_ve)} ${
              detail.gio_du_kien
            } · Phòng ${detail.phong}`}
          </Text>
        </div>

        {detail.bao_cao_cuoi ? (
          <Button onClick={() => void handleDownload()}>
            {`⬇ Tải báo cáo cuối (${detail.bao_cao_cuoi.dinh_dang}, ${formatBytes(detail.bao_cao_cuoi.kich_thuoc)})`}
          </Button>
        ) : (
          <Text type="secondary">Sinh viên chưa có báo cáo cuối</Text>
        )}

        <div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Tóm tắt kiểm tra trùng lặp</div>
          <CheckSummaryBlock detail={detail} />
        </div>

        {!detail.co_the_cham && detail.ly_do_khong_cham && (
          <Alert type="info" showIcon message={detail.ly_do_khong_cham} />
        )}

        <Form form={form} layout="vertical" disabled={!detail.co_the_cham}>
          <Form.Item
            label="Điểm (0-10)"
            name="diem"
            rules={[{ required: true, message: 'Vui lòng nhập điểm' }]}
          >
            <InputNumber min={0} max={10} step={0.1} precision={1} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item label="Nhận xét" name="nhan_xet" rules={[{ max: 5000, message: 'Tối đa 5000 ký tự' }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" loading={scoreMutation.isPending} onClick={() => void handleSave()}>
            Lưu điểm
          </Button>
        </Form>
      </Space>
    </Card>
  )
}

/**
 * MH-12/UC4.3: GV chỉ thấy các hội đồng mình là thành viên và chấm điểm
 * (0–10, một chữ số thập phân) cho SV trong hội đồng đó — server trả 403
 * cho GV ngoài hội đồng (UC4.3 E1) và 409 khi đã chốt/chưa đến ngày.
 */
export default function ScoringPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: committees, isLoading, isError, error, refetch: refetchCommittees } = useMyCommittees()

  const rawHoiDong = searchParams.get('hoi_dong_id')
  const rawLich = searchParams.get('lich_id')
  const selectedHoiDongId = rawHoiDong ? Number(rawHoiDong) : committees?.[0]?.id
  const selectedLichId = rawLich ? Number(rawLich) : undefined
  const selectedCommittee = (committees ?? []).find((c) => c.id === selectedHoiDongId)

  const selectCommittee = (id: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('hoi_dong_id', String(id))
    next.delete('lich_id')
    setSearchParams(next, { replace: true })
  }

  const selectStudent = (lichId: number) => {
    const next = new URLSearchParams(searchParams)
    if (selectedHoiDongId !== undefined) next.set('hoi_dong_id', String(selectedHoiDongId))
    next.set('lich_id', String(lichId))
    setSearchParams(next, { replace: true })
  }

  if (isError) {
    const status = error instanceof AxiosError ? error.response?.status : undefined
    if (status === 403) return <ForbiddenPage />
    // WR-12: lỗi khác 403 không được hiển thị như "chưa được phân hội đồng".
    return (
      <Card title="Hội đồng của tôi">
        <QueryErrorAlert error={error} onRetry={() => void refetchCommittees()} />
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }

  if (!committees || committees.length === 0) {
    return (
      <Card title="Hội đồng của tôi">
        <Empty description="Bạn chưa được phân vào hội đồng nào" />
        <p style={{ marginTop: 12, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
          Chỉ hiển thị các hội đồng mà bạn là thành viên (UC4.3).
        </p>
      </Card>
    )
  }

  const studentColumns: ColumnsType<MyCommitteeRow> = [
    {
      title: 'Sinh viên',
      key: 'sinh_vien',
      render: (_value, record) => (
        <span>
          {record.sinh_vien.ho_ten}
          {record.da_chot && (
            <Tag color="success" style={{ marginLeft: 8 }}>
              Đã chốt
            </Tag>
          )}
        </span>
      ),
    },
    { title: 'Đề tài', dataIndex: 'ten_de_tai' },
    { title: 'Giờ', dataIndex: 'gio_du_kien', width: 70 },
    {
      title: 'Điểm của tôi',
      key: 'diem_cua_toi',
      width: 110,
      render: (_value, record) =>
        record.diem_cua_toi !== null ? record.diem_cua_toi.toFixed(1) : <Tag>Chưa chấm</Tag>,
    },
  ]

  return (
    <Row gutter={20}>
      <Col xs={24} lg={11}>
        <Card title="Hội đồng của tôi" style={{ marginBottom: 20 }}>
          <List<MyCommittee>
            dataSource={committees}
            renderItem={(item) => (
              <List.Item
                onClick={() => selectCommittee(item.id)}
                style={{
                  cursor: 'pointer',
                  background: selectedHoiDongId === item.id ? 'rgba(22,119,255,0.06)' : undefined,
                  padding: '8px 12px',
                }}
              >
                {committeeLabel(item)}
              </List.Item>
            )}
          />
          <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
            Chỉ hiển thị các hội đồng mà bạn là thành viên (UC4.3).
          </p>
        </Card>

        <Card title="Sinh viên trong hội đồng">
          <Table<MyCommitteeRow>
            size="small"
            rowKey="id"
            pagination={false}
            columns={studentColumns}
            dataSource={selectedCommittee?.lich ?? []}
            locale={{ emptyText: 'Chưa có sinh viên trong hội đồng' }}
            onRow={(record) => ({
              onClick: () => selectStudent(record.id),
              style: {
                cursor: 'pointer',
                background: selectedLichId === record.id ? 'rgba(22,119,255,0.06)' : undefined,
              },
            })}
          />
        </Card>
      </Col>

      <Col xs={24} lg={13}>
        {selectedLichId !== undefined ? (
          <ScoringPanel key={selectedLichId} lichId={selectedLichId} />
        ) : (
          <Card>
            <Empty description="Chọn một sinh viên trong hội đồng để chấm điểm" />
          </Card>
        )}
      </Col>
    </Row>
  )
}
