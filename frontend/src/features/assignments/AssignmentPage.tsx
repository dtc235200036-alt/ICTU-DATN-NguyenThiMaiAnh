import { useEffect, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Input,
  Modal,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Upload,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useLecturers } from '../accounts/api'
import { useCohorts } from '../cohorts/api'
import { TRANG_THAI_DE_TAI } from '../topics/constants'
import { useAssignments, useImportAssignments, useUpdateAssignments } from './api'
import type { AssignmentFilter, AssignmentResult, AssignmentRow } from './api'

const { TextArea } = Input

const CSV_EXAMPLE = 'ma_so_sinh_vien,ma_giang_vien\nDTC235200016,GV001\nDTC235200036,GV001'

/**
 * MH-15/UC0.8: Bộ môn phân công GVHD theo đợt — mỗi SV đúng một GVHD. Đổi
 * GVHD ngay trên từng dòng, gán hàng loạt cho các dòng đã chọn, hoặc import
 * CSV `ma_so_sinh_vien,ma_giang_vien`. Dòng có đề tài Đã phân công bị khóa
 * (server trả 409 nếu cố đổi) vì đề cương/tiến độ/bảo vệ đã bám GVHD đó.
 */
export default function AssignmentPage() {
  const { message } = AntApp.useApp()

  const { data: cohorts } = useCohorts()
  const { data: lecturers } = useLecturers()
  const [dotDoAnId, setDotDoAnId] = useState<number | undefined>(undefined)
  const [q, setQ] = useState('')
  const [loc, setLoc] = useState<AssignmentFilter>('tat_ca')
  const [gvFilter, setGvFilter] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selected, setSelected] = useState<number[]>([])
  const [bulkGv, setBulkGv] = useState<number | undefined>(undefined)
  const [importOpen, setImportOpen] = useState(false)
  const [csvText, setCsvText] = useState('')
  const [importResult, setImportResult] = useState<AssignmentResult | null>(null)

  // Mặc định: đợt đang mở mới nhất (cohorts trả mới nhất trước).
  useEffect(() => {
    if (dotDoAnId === undefined && cohorts && cohorts.length > 0) {
      const open = cohorts.find((c) => c.trang_thai === 'DANG_MO') ?? cohorts[0]
      setDotDoAnId(open.id)
    }
  }, [cohorts, dotDoAnId])

  const { data, isFetching } = useAssignments(
    dotDoAnId === undefined
      ? undefined
      : {
          dot_do_an_id: dotDoAnId,
          q: q || undefined,
          loc,
          giang_vien_id: gvFilter,
          page,
          page_size: pageSize,
        },
  )
  const updateMutation = useUpdateAssignments()
  const importMutation = useImportAssignments()

  const gvOptions = (lecturers ?? []).map((gv) => ({
    value: gv.id,
    label: [gv.hoc_vi, gv.ho_ten].filter(Boolean).join(' ') + (gv.ma_giang_vien ? ` (${gv.ma_giang_vien})` : ''),
  }))
  const loadByGv = new Map((data?.tai_giang_vien ?? []).map((x) => [x.giang_vien.id, x.so_sinh_vien]))
  const gvOptionsWithLoad = gvOptions.map((o) => ({
    ...o,
    label: `${o.label} — ${loadByGv.get(o.value) ?? 0} SV`,
  }))

  const save = async (items: { sinh_vien_id: number; giang_vien_id: number | null }[]) => {
    if (dotDoAnId === undefined) return
    try {
      const res = await updateMutation.mutateAsync({ dot_do_an_id: dotDoAnId, items })
      message.success(res.cap_nhat > 0 ? `Đã cập nhật ${res.cap_nhat} phân công` : 'Không có thay đổi')
      setSelected([])
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleImport = async () => {
    if (dotDoAnId === undefined) return
    try {
      const res = await importMutation.mutateAsync({ dot_do_an_id: dotDoAnId, noi_dung: csvText })
      setImportResult(res)
      message.success(`Đã cập nhật ${res.cap_nhat} phân công`)
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const closeImport = () => {
    setImportOpen(false)
    setCsvText('')
    setImportResult(null)
  }

  const columns: ColumnsType<AssignmentRow> = [
    { title: 'Mã SV', key: 'ma', render: (_v, r) => r.sinh_vien.ma ?? '—', width: 140 },
    { title: 'Họ tên', key: 'ho_ten', render: (_v, r) => r.sinh_vien.ho_ten },
    { title: 'Lớp', dataIndex: 'lop', render: (v: string | null) => v ?? '—', width: 120 },
    {
      title: 'Giảng viên hướng dẫn',
      key: 'gv',
      width: 340,
      render: (_v, r) => {
        const select = (
          <Select
            showSearch
            allowClear
            style={{ width: '100%' }}
            placeholder="Chưa phân công"
            value={r.giang_vien?.id}
            disabled={!r.doi_duoc || updateMutation.isPending}
            options={gvOptionsWithLoad}
            optionFilterProp="label"
            onChange={(value: number | undefined) =>
              void save([{ sinh_vien_id: r.sinh_vien.id, giang_vien_id: value ?? null }])
            }
          />
        )
        return r.doi_duoc ? (
          select
        ) : (
          <Tooltip title="Sinh viên đã có đề tài Đã phân công — không đổi được GVHD">{select}</Tooltip>
        )
      },
    },
    {
      title: 'Đề tài',
      key: 'de_tai',
      render: (_v, r) =>
        r.de_tai_id ? (
          <Space size={4} wrap>
            <Tag color={TRANG_THAI_DE_TAI[r.trang_thai_de_tai ?? '']?.color}>
              {TRANG_THAI_DE_TAI[r.trang_thai_de_tai ?? '']?.label ?? r.trang_thai_de_tai}
            </Tag>
            <Link to={`/de-tai/${r.de_tai_id}`}>{r.ten_de_tai}</Link>
          </Space>
        ) : (
          <span style={{ color: 'rgba(0,0,0,0.45)' }}>Chưa có</span>
        ),
    },
  ]

  const chuaPhanCong = data ? data.tong_sinh_vien - data.da_phan_cong : 0

  return (
    <div>
      <Card
        title="Phân công giảng viên hướng dẫn"
        extra={
          <Space>
            <Select
              style={{ width: 300 }}
              placeholder="Chọn đợt đồ án"
              value={dotDoAnId}
              onChange={(value: number) => {
                setDotDoAnId(value)
                setPage(1)
                setSelected([])
              }}
              options={(cohorts ?? []).map((c) => ({
                value: c.id,
                label: `${c.ten_dot} (${c.khoa})`,
              }))}
            />
            <Button onClick={() => setImportOpen(true)} disabled={dotDoAnId === undefined}>
              Import CSV
            </Button>
          </Space>
        }
      >
        <Space size={48} style={{ marginBottom: 16 }} wrap>
          <Statistic title="Tổng sinh viên" value={data?.tong_sinh_vien ?? 0} />
          <Statistic title="Đã phân công" value={data?.da_phan_cong ?? 0} />
          <Statistic
            title="Chưa phân công"
            value={chuaPhanCong}
            valueStyle={chuaPhanCong > 0 ? { color: '#d46b08' } : undefined}
          />
        </Space>

        <Space style={{ marginBottom: 16 }} wrap>
          <Input.Search
            allowClear
            placeholder="Tìm mã SV, họ tên, lớp"
            style={{ width: 260 }}
            onSearch={(value) => {
              setQ(value.trim())
              setPage(1)
            }}
          />
          <Select<AssignmentFilter>
            style={{ width: 180 }}
            value={loc}
            onChange={(value) => {
              setLoc(value)
              setPage(1)
            }}
            options={[
              { value: 'tat_ca', label: 'Tất cả sinh viên' },
              { value: 'chua_phan_cong', label: 'Chưa phân công' },
              { value: 'da_phan_cong', label: 'Đã phân công' },
            ]}
          />
          <Select
            allowClear
            showSearch
            style={{ width: 300 }}
            placeholder="Lọc theo GVHD"
            value={gvFilter}
            optionFilterProp="label"
            onChange={(value: number | undefined) => {
              setGvFilter(value)
              setPage(1)
            }}
            options={gvOptionsWithLoad}
          />
        </Space>

        {selected.length > 0 && (
          <Alert
            type="info"
            style={{ marginBottom: 16 }}
            message={
              <Space wrap>
                <span>Đã chọn {selected.length} sinh viên —</span>
                <Select
                  showSearch
                  style={{ width: 320 }}
                  placeholder="Chọn GVHD"
                  value={bulkGv}
                  optionFilterProp="label"
                  onChange={(value: number) => setBulkGv(value)}
                  options={gvOptionsWithLoad}
                />
                <Button
                  type="primary"
                  disabled={bulkGv === undefined}
                  loading={updateMutation.isPending}
                  onClick={() =>
                    void save(selected.map((id) => ({ sinh_vien_id: id, giang_vien_id: bulkGv ?? null })))
                  }
                >
                  Gán cho GVHD này
                </Button>
                <Button
                  danger
                  loading={updateMutation.isPending}
                  onClick={() => void save(selected.map((id) => ({ sinh_vien_id: id, giang_vien_id: null })))}
                >
                  Gỡ phân công
                </Button>
              </Space>
            }
          />
        )}

        <Table<AssignmentRow>
          rowKey={(r) => r.sinh_vien.id}
          loading={isFetching}
          columns={columns}
          dataSource={data?.items ?? []}
          rowSelection={{
            selectedRowKeys: selected,
            onChange: (keys) => setSelected(keys as number[]),
            getCheckboxProps: (r) => ({ disabled: !r.doi_duoc }),
          }}
          locale={{ emptyText: 'Không có sinh viên' }}
          pagination={{
            current: page,
            pageSize,
            total: data?.total ?? 0,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPage)
              setPageSize(nextPageSize)
            },
          }}
        />
      </Card>

      <Modal
        open={importOpen}
        title="Import phân công GVHD từ CSV"
        onCancel={closeImport}
        width={620}
        footer={[
          <Button key="close" onClick={closeImport}>
            Đóng
          </Button>,
          <Button
            key="import"
            type="primary"
            disabled={csvText.trim().length === 0}
            loading={importMutation.isPending}
            onClick={handleImport}
          >
            Import
          </Button>,
        ]}
      >
        <p style={{ marginTop: 0 }}>
          Mỗi dòng <code>ma_so_sinh_vien,ma_giang_vien</code> (dòng tiêu đề tùy chọn). Dòng sau
          ghi đè dòng trước cùng sinh viên; dòng lỗi được liệt kê, các dòng hợp lệ vẫn được lưu.
        </p>
        <Upload
          accept=".csv,.txt"
          maxCount={1}
          showUploadList={false}
          beforeUpload={(file) => {
            void file.text().then(setCsvText)
            return false
          }}
        >
          <Button style={{ marginBottom: 8 }}>Chọn tệp CSV…</Button>
        </Upload>
        <TextArea
          rows={8}
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
          placeholder={CSV_EXAMPLE}
        />
        {importResult && importResult.loi.length > 0 && (
          <Alert
            type="warning"
            showIcon
            style={{ marginTop: 12 }}
            message={`${importResult.loi.length} dòng không import được`}
            description={
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {importResult.loi.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            }
          />
        )}
      </Modal>
    </div>
  )
}
