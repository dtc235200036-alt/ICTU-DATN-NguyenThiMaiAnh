import { useEffect, useMemo, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Input,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AxiosError } from 'axios'
import { useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { DownloadError, downloadFile } from '../../api/download'
import { useAuthStore } from '../../stores/auth'
import { formatBytes, formatDate, formatDateTime } from '../../utils/format'
import ForbiddenPage from '../auth/ForbiddenPage'
import { useCohorts } from '../cohorts/api'
import { dinhHuongLabel } from '../dinh-huong/api'
import CheckPanel from '../documents/CheckPanel'
import CheckStatusTag from '../documents/CheckStatusTag'
import FilePreview from '../documents/FilePreview'
import {
  exportSignedOutlines,
  useBoMonApprove,
  useBoMonReturn,
  useForwardOutline,
  useOutline,
  useOutlineCounts,
  useOutlines,
  useReviewOutline,
} from './api'
import type { OutlineDetail, OutlineFilter, OutlineListItem, OutlineVersion } from './api'
import CheckList from './CheckList'
import { trangThaiDeCuong } from './constants'
import VersionHistory from './VersionHistory'

const { TextArea } = Input
const PAGE_SIZE = 10

type TabKey = 'TAT_CA' | OutlineFilter

function personLabel(p: { ho_ten: string; ma?: string | null } | null): string {
  if (!p) return '—'
  return p.ma ? `${p.ho_ten} (${p.ma})` : p.ho_ten
}

function versionLabel(version: OutlineVersion, isNewest: boolean): string {
  const base = `v${version.tai_lieu.so_phien_ban} - nộp ${formatDate(version.tai_lieu.thoi_diem_nop)}`
  return isNewest ? `${base} (mới nhất)` : base
}

/**
 * Danh sách đề cương + chi tiết duyệt cho GVHD và Lãnh đạo bộ môn.
 * - GVHD: duyệt/từ chối (yêu cầu sửa) phiên bản mới nhất, rồi "Nộp lên Bộ môn"
 *   khi tên file đúng quy tắc và định hướng khớp.
 * - Bộ môn: tab Tất cả/Chờ duyệt/Đã duyệt/Từ chối; phê duyệt bằng cách tải lên
 *   bản PDF đã ký số (lưu vào thư mục đề cương của đợt) hoặc trả lại.
 */
export default function OutlineReviewPage() {
  const user = useAuthStore((state) => state.user)
  const isBoMon = user?.vai_tro === 'BO_MON'

  const [searchParams, setSearchParams] = useSearchParams()
  const deTaiIdParam = searchParams.get('de_tai_id')
  const selectedId = deTaiIdParam ? Number(deTaiIdParam) : undefined

  const setParam = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
  }

  if (selectedId !== undefined) {
    return (
      <OutlineReviewDetail
        deTaiId={selectedId}
        isBoMon={isBoMon}
        onBack={() => setParam('de_tai_id', undefined)}
      />
    )
  }
  return (
    <OutlineList
      isBoMon={isBoMon}
      tab={(searchParams.get('tab') as TabKey | null) ?? (isBoMon ? 'CHO_BO_MON_DUYET' : 'CHO_DUYET')}
      onTab={(tab) => setParam('tab', tab)}
      onOpen={(id) => setParam('de_tai_id', String(id))}
    />
  )
}

function OutlineList({
  isBoMon,
  tab,
  onTab,
  onOpen,
}: {
  isBoMon: boolean
  tab: TabKey
  onTab: (tab: TabKey) => void
  onOpen: (deTaiId: number) => void
}) {
  const { message } = AntApp.useApp()
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const { data: cohorts } = useCohorts()

  useEffect(() => {
    if (dotDoAnId === undefined && cohorts && cohorts.length > 0) {
      setDotDoAnId((cohorts.find((c) => c.trang_thai === 'DANG_MO') ?? cohorts[0]).id)
    }
  }, [cohorts, dotDoAnId])

  useEffect(() => setPage(1), [tab, q, dotDoAnId])

  const listParams = {
    trang_thai: tab === 'TAT_CA' ? undefined : tab,
    dot_do_an_id: dotDoAnId,
    q: q || undefined,
    page,
    page_size: PAGE_SIZE,
  }
  const { data: outlinesPage, isFetching } = useOutlines(listParams)
  const { data: counts } = useOutlineCounts({ dot_do_an_id: dotDoAnId, q: q || undefined })
  const c = (key: keyof NonNullable<typeof counts>['theo_trang_thai']) =>
    counts?.theo_trang_thai[key] ?? 0

  const tabs: { key: TabKey; label: string }[] = isBoMon
    ? [
        { key: 'TAT_CA', label: `Tất cả (${counts?.tat_ca ?? 0})` },
        { key: 'CHO_BO_MON_DUYET', label: `Chờ duyệt (${c('CHO_BO_MON_DUYET')})` },
        { key: 'DA_DUYET', label: `Đã duyệt (${c('DA_DUYET')})` },
        { key: 'BO_MON_TRA_LAI', label: `Từ chối (${counts?.bo_mon_tra_lai ?? 0})` },
      ]
    : [
        { key: 'TAT_CA', label: `Tất cả (${counts?.tat_ca ?? 0})` },
        { key: 'CHO_DUYET', label: `Chờ duyệt (${c('CHO_DUYET')})` },
        { key: 'GVHD_DA_DUYET', label: `Chờ nộp Bộ môn (${c('GVHD_DA_DUYET')})` },
        { key: 'CHO_BO_MON_DUYET', label: `Đã nộp Bộ môn (${c('CHO_BO_MON_DUYET')})` },
        { key: 'DA_DUYET', label: `Đã duyệt (${c('DA_DUYET')})` },
        { key: 'YEU_CAU_SUA', label: `Yêu cầu sửa (${c('YEU_CAU_SUA')})` },
      ]

  const handleExport = async () => {
    if (dotDoAnId === undefined) return
    try {
      await exportSignedOutlines(dotDoAnId)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được thư mục đề cương')
    }
  }

  const columns: ColumnsType<OutlineListItem> = [
    {
      title: 'STT',
      key: 'stt',
      width: 60,
      render: (_v, _r, index) => (page - 1) * PAGE_SIZE + index + 1,
    },
    { title: 'Sinh viên', key: 'sinh_vien', render: (_v, r) => personLabel(r.sinh_vien) },
    { title: 'Tên đề tài', dataIndex: 'ten_de_tai' },
    ...(isBoMon
      ? ([
          {
            title: 'GVHD',
            key: 'giang_vien',
            render: (_v: unknown, r: OutlineListItem) => personLabel(r.giang_vien),
          },
        ] as ColumnsType<OutlineListItem>)
      : ([
          {
            title: 'File đề cương',
            key: 'file',
            render: (_v: unknown, r: OutlineListItem) =>
              r.phien_ban_moi_nhat ? (
                <span>
                  {r.phien_ban_moi_nhat.ten_goc}{' '}
                  <Typography.Text type="secondary">(v{r.phien_ban_moi_nhat.so_phien_ban})</Typography.Text>
                </span>
              ) : (
                '—'
              ),
          },
        ] as ColumnsType<OutlineListItem>)),
    {
      title: 'Ngày nộp',
      key: 'ngay_nop',
      width: 110,
      render: (_v, r) =>
        isBoMon && r.nop_bo_mon_luc
          ? formatDate(r.nop_bo_mon_luc)
          : formatDate(r.phien_ban_moi_nhat?.thoi_diem_nop),
    },
    {
      title: 'Kiểm tra trùng lặp',
      key: 'kiem_tra',
      render: (_v, r) => <CheckStatusTag kiemTra={r.kiem_tra} />,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trang_thai',
      render: (value: string, r) => {
        const info = trangThaiDeCuong(value)
        return (
          <Space size={4} wrap>
            <Tag color={info.color}>{info.label}</Tag>
            {r.ket_qua_bo_mon === 'TRA_LAI' && value === 'YEU_CAU_SUA' && (
              <Tag color="volcano">Bộ môn trả lại</Tag>
            )}
          </Space>
        )
      },
    },
    {
      title: 'Thao tác',
      key: 'thao_tac',
      width: 100,
      render: (_v, r) => {
        const action =
          (!isBoMon && (r.trang_thai === 'CHO_DUYET' || r.trang_thai === 'GVHD_DA_DUYET')) ||
          (isBoMon && r.trang_thai === 'CHO_BO_MON_DUYET')
        return (
          <Button size="small" type={action ? 'primary' : 'default'} onClick={() => onOpen(r.de_tai_id)}>
            {action ? 'Duyệt' : 'Xem'}
          </Button>
        )
      },
    },
  ]

  return (
    <Card
      title={isBoMon ? 'Danh sách đề cương chờ duyệt' : 'Danh sách đề cương sinh viên hướng dẫn'}
      extra={
        <Space wrap>
          <Select
            style={{ width: 300 }}
            placeholder="Đợt đồ án"
            value={dotDoAnId}
            onChange={(v: number) => setDotDoAnId(v)}
            options={(cohorts ?? []).map((co) => ({ value: co.id, label: co.ten_dot }))}
          />
          {isBoMon && (
            <Button onClick={() => void handleExport()} disabled={dotDoAnId === undefined}>
              Tải thư mục đề cương đã ký số
            </Button>
          )}
        </Space>
      }
    >
      <Input.Search
        allowClear
        placeholder="Tìm theo tên/mã sinh viên hoặc tên đề tài"
        style={{ maxWidth: 420, marginBottom: 8 }}
        onSearch={(value) => setQ(value.trim())}
      />
      <Tabs activeKey={tab} onChange={(k) => onTab(k as TabKey)} items={tabs} />
      <Table<OutlineListItem>
        rowKey="de_tai_id"
        loading={isFetching}
        columns={columns}
        dataSource={outlinesPage?.items ?? []}
        locale={{ emptyText: 'Không có đề cương nào' }}
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total: outlinesPage?.total ?? 0,
          onChange: setPage,
          showSizeChanger: false,
        }}
      />
    </Card>
  )
}

function OutlineReviewDetail({
  deTaiId,
  isBoMon,
  onBack,
}: {
  deTaiId: number
  isBoMon: boolean
  onBack: () => void
}) {
  const { message } = AntApp.useApp()
  const { data: detail, isError, error, refetch } = useOutline(deTaiId)
  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>(undefined)

  useEffect(() => {
    if (detail) setSelectedVersionId(detail.phien_ban[0]?.tai_lieu.id)
  }, [detail?.de_tai_id, detail?.phien_ban.length])

  const selectedVersion = useMemo(
    () => detail?.phien_ban.find((v) => v.tai_lieu.id === selectedVersionId),
    [detail, selectedVersionId],
  )

  if (isError) {
    const status = error instanceof AxiosError ? error.response?.status : undefined
    if (status === 403) return <ForbiddenPage />
  }

  const handleDownload = async (id: number, name: string) => {
    try {
      await downloadFile(`/documents/${id}/download`, name)
    } catch (err) {
      message.error(err instanceof DownloadError ? err.message : 'Không tải được file')
    }
  }

  return (
    <div>
      <Button style={{ marginBottom: 16 }} onClick={onBack}>
        ← Danh sách đề cương
      </Button>
      {detail && (
        <>
          <Row gutter={20}>
            <Col xs={24} xl={10}>
              <Card
                title="Chi tiết đề cương"
                extra={
                  <Tag color={trangThaiDeCuong(detail.trang_thai).color}>
                    {trangThaiDeCuong(detail.trang_thai).label}
                  </Tag>
                }
              >
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="Sinh viên">{personLabel(detail.sinh_vien)}</Descriptions.Item>
                  <Descriptions.Item label="Lớp">{detail.lop ?? '—'}</Descriptions.Item>
                  <Descriptions.Item label="Tên đề tài">{detail.ten_de_tai}</Descriptions.Item>
                  <Descriptions.Item label="Định hướng">{dinhHuongLabel(detail.dinh_huong)}</Descriptions.Item>
                  <Descriptions.Item label="GVHD">{personLabel(detail.giang_vien)}</Descriptions.Item>
                  <Descriptions.Item label="Phiên bản">
                    <Select
                      size="small"
                      style={{ width: '100%' }}
                      value={selectedVersionId}
                      onChange={(v: number) => setSelectedVersionId(v)}
                      options={detail.phien_ban.map((v, idx) => ({
                        value: v.tai_lieu.id,
                        label: versionLabel(v, idx === 0),
                      }))}
                    />
                  </Descriptions.Item>
                  {selectedVersion && (
                    <>
                      <Descriptions.Item label="File đề cương">
                        <Button
                          type="link"
                          style={{ padding: 0, height: 'auto', whiteSpace: 'normal', textAlign: 'left' }}
                          onClick={() =>
                            void handleDownload(selectedVersion.tai_lieu.id, selectedVersion.tai_lieu.ten_goc)
                          }
                        >
                          ⬇ {selectedVersion.tai_lieu.ten_goc} ({formatBytes(selectedVersion.tai_lieu.kich_thuoc)})
                        </Button>
                      </Descriptions.Item>
                      <Descriptions.Item label="Ngày nộp">
                        {formatDateTime(selectedVersion.tai_lieu.thoi_diem_nop)}
                      </Descriptions.Item>
                      {selectedVersion.tai_lieu.ghi_chu && (
                        <Descriptions.Item label="Ghi chú của SV">{selectedVersion.tai_lieu.ghi_chu}</Descriptions.Item>
                      )}
                    </>
                  )}
                  {detail.nop_bo_mon_luc && (
                    <Descriptions.Item label="Nộp lên Bộ môn">{formatDateTime(detail.nop_bo_mon_luc)}</Descriptions.Item>
                  )}
                </Descriptions>

                <Typography.Title level={5} style={{ marginTop: 20 }}>
                  Kiểm tra trước khi nộp lên khoa
                </Typography.Title>
                <CheckList items={detail.kiem_tra_nop} />

                <ActionPanel
                  detail={detail}
                  isBoMon={isBoMon}
                  selectedVersion={selectedVersion}
                  onDone={() => void refetch()}
                />

                <BoMonHistory detail={detail} onDownload={handleDownload} />
              </Card>
            </Col>
            <Col xs={24} xl={14}>
              <Card title="Xem file đề cương" style={{ marginBottom: 20 }}>
                <FilePreview doc={selectedVersion?.tai_lieu} />
              </Card>
              <CheckPanel taiLieuId={selectedVersion?.tai_lieu.id} canRecheck />
            </Col>
          </Row>
          <div style={{ marginTop: 20 }}>
            <VersionHistory versions={detail.phien_ban} trangThai={detail.trang_thai} docLabel="đề cương" />
          </div>
        </>
      )}
    </div>
  )
}

function ActionPanel({
  detail,
  isBoMon,
  selectedVersion,
  onDone,
}: {
  detail: OutlineDetail
  isBoMon: boolean
  selectedVersion: OutlineVersion | undefined
  onDone: () => void
}) {
  const { message } = AntApp.useApp()
  const [nhanXet, setNhanXet] = useState('')
  const [signedFile, setSignedFile] = useState<File | null>(null)
  const review = useReviewOutline()
  const forward = useForwardOutline()
  const approve = useBoMonApprove()
  const giveBack = useBoMonReturn()
  const isNewest = detail.phien_ban[0]?.tai_lieu.id === selectedVersion?.tai_lieu.id
  const blocking = detail.kiem_tra_nop.filter((c) => c.ma !== 'NOI_DUNG' && !c.dat)

  const run = async (action: () => Promise<unknown>, ok: string) => {
    try {
      await action()
      message.success(ok)
      setNhanXet('')
      setSignedFile(null)
    } catch (err) {
      message.error(getErrorMessage(err))
    } finally {
      onDone()
    }
  }

  if (!isBoMon && detail.quyen.duyet && isNewest && selectedVersion) {
    return (
      <div style={{ marginTop: 20 }}>
        <Typography.Title level={5}>Duyệt đề cương</Typography.Title>
        <TextArea
          rows={3}
          maxLength={5000}
          placeholder="Nhận xét (bắt buộc khi từ chối)"
          value={nhanXet}
          onChange={(e) => setNhanXet(e.target.value)}
        />
        <Space style={{ marginTop: 12 }}>
          <Button
            danger
            disabled={nhanXet.trim().length === 0}
            loading={review.isPending}
            onClick={() =>
              void run(
                () =>
                  review.mutateAsync({
                    deTaiId: detail.de_tai_id,
                    taiLieuDoAnId: selectedVersion.tai_lieu.id,
                    ketQua: 'YEU_CAU_SUA',
                    nhanXet: nhanXet.trim(),
                  }),
                'Đã từ chối — sinh viên sẽ sửa và nộp lại',
              )
            }
          >
            Từ chối
          </Button>
          <Popconfirm
            title="Duyệt đề cương này?"
            onConfirm={() =>
              void run(
                () =>
                  review.mutateAsync({
                    deTaiId: detail.de_tai_id,
                    taiLieuDoAnId: selectedVersion.tai_lieu.id,
                    ketQua: 'DA_DUYET',
                    nhanXet: nhanXet.trim() || undefined,
                  }),
                'Đã duyệt — bước tiếp theo: nộp đề cương lên Bộ môn',
              )
            }
          >
            <Button type="primary" loading={review.isPending}>
              Duyệt
            </Button>
          </Popconfirm>
        </Space>
      </div>
    )
  }

  if (!isBoMon && detail.quyen.nop_bo_mon) {
    return (
      <div style={{ marginTop: 20 }}>
        {blocking.length > 0 ? (
          <Alert
            type="warning"
            showIcon
            message="Chưa thể nộp lên Bộ môn"
            description="Tên file hoặc định hướng chưa đúng. Hãy yêu cầu sinh viên đặt lại tên file và nộp lại."
          />
        ) : (
          <Alert type="success" showIcon message="Đề cương đã đạt các mục kiểm tra, sẵn sàng nộp lên Bộ môn" />
        )}
        <Popconfirm
          title="Nộp đề cương này lên Bộ môn duyệt?"
          onConfirm={() =>
            void run(() => forward.mutateAsync({ deTaiId: detail.de_tai_id }), 'Đã nộp đề cương lên Bộ môn')
          }
          disabled={blocking.length > 0}
        >
          <Button
            type="primary"
            block
            style={{ marginTop: 12 }}
            disabled={blocking.length > 0}
            loading={forward.isPending}
          >
            Nộp file đề cương lên Bộ môn
          </Button>
        </Popconfirm>
      </div>
    )
  }

  if (isBoMon && detail.quyen.duyet_bo_mon) {
    return (
      <div style={{ marginTop: 20 }}>
        <Typography.Title level={5}>Phê duyệt và nộp về khoa</Typography.Title>
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="Các bước"
          description={
            <ol style={{ margin: 0, paddingLeft: 18 }}>
              <li>Kiểm tra tên file, nội dung và định hướng (mục kiểm tra ở trên).</li>
              <li>Tải file đề cương, ký số bằng công cụ ký số (USB token, VNPT-CA, Adobe…), lưu thành PDF.</li>
              <li>Tải bản PDF đã ký lên đây — hệ thống kiểm tra chữ ký và lưu vào thư mục đề cương của đợt.</li>
            </ol>
          }
        />
        <Upload.Dragger
          accept=".pdf"
          maxCount={1}
          beforeUpload={(file) => {
            setSignedFile(file)
            return false
          }}
          onRemove={() => setSignedFile(null)}
          fileList={
            signedFile ? [{ uid: '-1', name: signedFile.name, status: 'done', size: signedFile.size }] : []
          }
        >
          <p className="ant-upload-text">Kéo thả bản PDF đã ký số hoặc bấm để chọn</p>
        </Upload.Dragger>
        <TextArea
          rows={3}
          maxLength={5000}
          style={{ marginTop: 12 }}
          placeholder="Nhận xét (bắt buộc khi trả lại)"
          value={nhanXet}
          onChange={(e) => setNhanXet(e.target.value)}
        />
        <Space style={{ marginTop: 12 }}>
          <Button
            danger
            disabled={nhanXet.trim().length === 0}
            loading={giveBack.isPending}
            onClick={() =>
              void run(
                () => giveBack.mutateAsync({ deTaiId: detail.de_tai_id, nhanXet: nhanXet.trim() }),
                'Đã trả lại đề cương',
              )
            }
          >
            Từ chối
          </Button>
          <Button
            type="primary"
            disabled={!signedFile}
            loading={approve.isPending}
            onClick={() =>
              signedFile &&
              void run(
                () =>
                  approve.mutateAsync({
                    deTaiId: detail.de_tai_id,
                    file: signedFile,
                    nhanXet: nhanXet.trim() || undefined,
                  }),
                'Đã phê duyệt và lưu đề cương đã ký số',
              )
            }
          >
            Phê duyệt
          </Button>
        </Space>
      </div>
    )
  }
  return null
}

function BoMonHistory({
  detail,
  onDownload,
}: {
  detail: OutlineDetail
  onDownload: (id: number, name: string) => Promise<void>
}) {
  if (detail.luot_duyet_bo_mon.length === 0) return null
  return (
    <div style={{ marginTop: 20 }}>
      <Typography.Title level={5}>Ý kiến Bộ môn</Typography.Title>
      {detail.luot_duyet_bo_mon.map((r, idx) => (
        <Alert
          key={idx}
          style={{ marginBottom: 8 }}
          type={r.ket_qua === 'DA_DUYET' ? 'success' : 'warning'}
          showIcon
          message={`${r.ket_qua === 'DA_DUYET' ? 'Đã phê duyệt' : 'Trả lại'} — ${formatDateTime(r.thoi_diem)}`}
          description={
            <div>
              {r.nhan_xet && <div>{r.nhan_xet}</div>}
              {r.nguoi_ky && (
                <div>
                  Chữ ký số: {r.nguoi_ky}
                  {r.thoi_diem_ky ? ` (${formatDateTime(r.thoi_diem_ky)})` : ''}
                </div>
              )}
              {r.tai_lieu_ky_so && (
                <Button
                  type="link"
                  style={{ padding: 0 }}
                  onClick={() => void onDownload(r.tai_lieu_ky_so!.id, r.tai_lieu_ky_so!.ten_goc)}
                >
                  ⬇ Bản đề cương đã ký số
                </Button>
              )}
            </div>
          }
        />
      ))}
    </div>
  )
}
