import { useEffect, useRef, useState } from 'react'
import { App as AntApp, Alert, Button, Card, Form, Input, Select, Tag, Upload } from 'antd'
import type { InputRef } from 'antd'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import { useMyStudents } from '../assignments/api'
import { useCohorts } from '../cohorts/api'
import ForbiddenPage from '../auth/ForbiddenPage'
import { dinhHuongLabel, useDinhHuong } from '../dinh-huong/api'
import TitleCheckAlert from './TitleCheckAlert'
import {
  useAttachTopicFile,
  useCheckTitle,
  useCreateTopic,
  useSubmitTopic,
  useTopic,
  useUpdateTopic,
} from './api'
import type { TitleCheckResult, TopicFormInput } from './api'

const { TextArea } = Input

interface FormValues {
  dot_do_an_id: number
  ten_de_tai: string
  dinh_huong_id?: number
  mo_ta?: string
  sinh_vien_id: number
}

/**
 * MH-06 (UC1.1): GVHD tạo và giao đề tài ('/de-tai/de-xuat') hoặc sửa nháp
 * ('/de-tai/:id/sua'). Cùng một component cho cả hai chế độ — phân biệt qua
 * có/không có :id trên URL. Góp ý GVHD mục 1: SV không tự đề xuất/đăng ký; SV
 * và GV thống nhất đề tài ngoài hệ thống, GVHD (được Bộ môn phân công, UC0.8)
 * chọn một SV trong lớp hướng dẫn (bắt buộc) và giao -> Đã phân công
 * (?dot_do_an_id=&sinh_vien_id= điền sẵn từ "Sinh viên của tôi").
 */
export default function TopicFormPage() {
  const { id } = useParams()
  const editing = id !== undefined
  const topicId = editing ? Number(id) : undefined
  const navigate = useNavigate()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm<FormValues>()
  const titleInputRef = useRef<InputRef>(null)
  const [searchParams] = useSearchParams()
  const vaiTro = useAuthStore((s) => s.user?.vai_tro)
  const isGv = vaiTro === 'GIANG_VIEN'
  const selectedCohort = Form.useWatch('dot_do_an_id', form)

  const { data: cohorts, isLoading: cohortsLoading } = useCohorts({ trang_thai: 'DANG_MO' })
  const { data: topic, isLoading: topicLoading, isFetched: topicFetched } = useTopic(topicId)
  const { data: myStudents } = useMyStudents(selectedCohort, isGv && selectedCohort !== undefined)

  const createMutation = useCreateTopic()
  const updateMutation = useUpdateTopic()
  const submitMutation = useSubmitTopic()
  const checkTitleMutation = useCheckTitle()
  const attachMutation = useAttachTopicFile()
  const { data: dinhHuong, isLoading: dinhHuongLoading } = useDinhHuong(true)
  const [tepDinhKem, setTepDinhKem] = useState<File | null>(null)

  // UC0.6/FR-DT-02: kết quả kiểm tra trùng tên tức thời (chưa lưu — bản lưu
  // chỉ xảy ra khi GVHD thật sự giao đề tài, ở service topics.py).
  const [checkResult, setCheckResult] = useState<TitleCheckResult | null>(null)
  const [lastCheckedTitle, setLastCheckedTitle] = useState<string | null>(null)
  const [acknowledged, setAcknowledged] = useState(false)

  useEffect(() => {
    if (editing && topic) {
      form.setFieldsValue({
        dot_do_an_id: topic.dot_do_an.id,
        ten_de_tai: topic.ten_de_tai,
        dinh_huong_id: topic.dinh_huong?.id,
        mo_ta: topic.mo_ta ?? undefined,
        sinh_vien_id: topic.sinh_vien?.id,
      })
      setLastCheckedTitle(topic.ten_de_tai)
    }
  }, [editing, topic, form])

  // Từ "Sinh viên của tôi" -> "Giao đề tài": điền sẵn đợt + SV.
  useEffect(() => {
    if (editing) return
    const dot = Number(searchParams.get('dot_do_an_id'))
    const sv = Number(searchParams.get('sinh_vien_id'))
    if (dot > 0) form.setFieldValue('dot_do_an_id', dot)
    if (sv > 0) form.setFieldValue('sinh_vien_id', sv)
  }, [editing, searchParams, form])

  if (editing && topicLoading && !topicFetched) {
    return null
  }

  if (editing && topic && !topic.quyen.sua) {
    return <ForbiddenPage />
  }

  const cohortOptions = (cohorts ?? []).map((c) => ({
    value: c.id,
    label: `${c.ten_dot} (${c.khoa})`,
  }))
  const noCohortOpen = !cohortsLoading && cohortOptions.length === 0

  // UC0.8: GVHD chỉ giao cho SV lớp mình chưa có đề tài đang hoạt động (khi sửa
  // nháp vẫn giữ SV đang được chọn trong danh sách).
  const editingSvId = topic?.sinh_vien?.id
  const classOptions = (myStudents?.[0]?.items ?? [])
    .filter(
      (st) =>
        st.sinh_vien.id === editingSvId ||
        (st.trang_thai_de_tai !== 'DA_PHAN_CONG' && st.trang_thai_de_tai !== 'CHO_DUYET'),
    )
    .map((st) => ({
      value: st.sinh_vien.id,
      label: `${st.sinh_vien.ho_ten} (${st.sinh_vien.ma ?? ''})`,
    }))
  const submitLabel = 'Giao đề tài cho sinh viên'

  const buildInput = (values: FormValues): TopicFormInput => ({
    dot_do_an_id: values.dot_do_an_id,
    ten_de_tai: values.ten_de_tai,
    linh_vuc: topic?.linh_vuc ?? null,
    dinh_huong_id: values.dinh_huong_id ?? null,
    mo_ta: values.mo_ta ?? null,
    sinh_vien_id: values.sinh_vien_id,
  })

  const isSaving =
    createMutation.isPending ||
    updateMutation.isPending ||
    submitMutation.isPending ||
    attachMutation.isPending

  // File đính kèm gửi sau khi đề tài đã có id (lưu nháp hoặc giao).
  const uploadAttachment = async (savedId: number | undefined) => {
    if (tepDinhKem === null || savedId === undefined) return
    try {
      await attachMutation.mutateAsync({ id: savedId, file: tepDinhKem })
      setTepDinhKem(null)
    } catch (err) {
      message.warning(`Đề tài đã lưu nhưng chưa đính kèm được file: ${getErrorMessage(err)}`)
    }
  }

  // Mọi lần đổi tên đề tài làm kết quả cũ (và xác nhận "vẫn giao") hết hiệu lực
  // (UC1.1 A1/A2) — check tiếp theo chạy khi rời ô (onBlur) hoặc lúc gửi.
  const handleTitleChange = () => {
    if (acknowledged) {
      setAcknowledged(false)
    }
  }

  const handleTitleBlur = async () => {
    const title = form.getFieldValue('ten_de_tai') as string | undefined
    if (!title || title.length < 5 || title === lastCheckedTitle) {
      return
    }
    try {
      const result = await checkTitleMutation.mutateAsync(title)
      setCheckResult(result)
      setLastCheckedTitle(title)
      setAcknowledged(false)
    } catch {
      // Lỗi mạng khi kiểm tra tức thời không chặn người dùng tiếp tục điền form.
    }
  }

  const ensureTitleChecked = async (title: string): Promise<TitleCheckResult | null> => {
    if (checkResult !== null && lastCheckedTitle === title) {
      return checkResult
    }
    try {
      const result = await checkTitleMutation.mutateAsync(title)
      setCheckResult(result)
      setLastCheckedTitle(title)
      setAcknowledged(false)
      return result
    } catch (err) {
      message.error(getErrorMessage(err))
      return null
    }
  }

  const handleSaveDraft = async () => {
    let values: FormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }

    try {
      let savedId = topicId
      if (editing && topicId !== undefined) {
        await updateMutation.mutateAsync({ id: topicId, input: buildInput(values) })
      } else {
        const created = await createMutation.mutateAsync({ ...buildInput(values), gui: false })
        savedId = created.id
      }
      await uploadAttachment(savedId)
      message.success('Đã lưu nháp đề tài')
      if (savedId !== undefined) {
        navigate(`/de-tai/${savedId}`)
      }
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const doAssign = async (values: FormValues) => {
    try {
      let savedId = topicId
      if (editing && topicId !== undefined) {
        await updateMutation.mutateAsync({ id: topicId, input: buildInput(values) })
        await submitMutation.mutateAsync(topicId)
      } else {
        const created = await createMutation.mutateAsync({ ...buildInput(values), gui: true })
        savedId = created.id
      }
      await uploadAttachment(savedId)
      message.success('Đã giao đề tài cho sinh viên')
      if (savedId !== undefined) {
        navigate(`/de-tai/${savedId}`)
      }
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleAssign = async () => {
    let values: FormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }

    // UC1.1: kiểm tra lại nếu tên đã đổi kể từ lần kiểm tra gần nhất; nếu có
    // cảnh báo chưa xác nhận thì dừng lại ở đây, để TitleCheckAlert hiển thị.
    const result = await ensureTitleChecked(values.ten_de_tai)
    if (result === null) {
      return
    }
    if (result.trang_thai === 'HOAN_TAT' && result.matches.length > 0 && !acknowledged) {
      return
    }

    await doAssign(values)
  }

  const handleEditTitle = () => {
    titleInputRef.current?.focus()
  }

  const handleSendAnyway = () => {
    setAcknowledged(true)
  }

  return (
    <Card title="Thông tin đề tài">
      {noCohortOpen && (
        <Alert
          type="warning"
          showIcon
          message="Hiện không có đợt đồ án nào đang mở"
          style={{ marginBottom: 16 }}
        />
      )}
      <Form form={form} layout="vertical">
        <Form.Item
          label="Đợt đồ án"
          name="dot_do_an_id"
          extra="Chỉ hiển thị các đợt đang mở."
          rules={[{ required: true, message: 'Vui lòng chọn đợt đồ án' }]}
        >
          <Select
            options={cohortOptions}
            loading={cohortsLoading}
            disabled={noCohortOpen}
            placeholder="Chọn đợt đồ án"
          />
        </Form.Item>

        <Form.Item
          label="Tên đề tài"
          name="ten_de_tai"
          rules={[
            { required: true, message: 'Vui lòng nhập tên đề tài' },
            { min: 5, message: 'Tên đề tài tối thiểu 5 ký tự' },
            { max: 255, message: 'Tên đề tài tối đa 255 ký tự' },
          ]}
        >
          <Input
            ref={titleInputRef}
            maxLength={255}
            onChange={handleTitleChange}
            onBlur={handleTitleBlur}
          />
        </Form.Item>

        {checkResult && (
          <>
            {acknowledged && checkResult.matches.length > 0 ? (
              <Tag color="warning" style={{ marginBottom: 16 }}>
                Đã xác nhận giao kèm cảnh báo
              </Tag>
            ) : (
              <TitleCheckAlert
                result={checkResult}
                onEditTitle={handleEditTitle}
                onSendAnyway={handleSendAnyway}
              />
            )}
          </>
        )}

        <Form.Item
          label="Giao cho sinh viên"
          name="sinh_vien_id"
          extra="Chỉ sinh viên trong lớp hướng dẫn của bạn (chưa có đề tài), đã thống nhất đề tài với bạn."
          rules={[{ required: true, message: 'Vui lòng chọn sinh viên được giao' }]}
        >
          <Select
            showSearch
            optionFilterProp="label"
            placeholder="Chọn sinh viên trong lớp hướng dẫn"
            disabled={selectedCohort === undefined}
            options={classOptions}
          />
        </Form.Item>

        <Form.Item
          label="Định hướng"
          name="dinh_huong_id"
          extra="Mã định hướng là phần đầu tên file đề cương của sinh viên (vd. H01.MSSV.Họ tên.Lớp)."
          rules={[{ required: true, message: 'Vui lòng chọn định hướng' }]}
        >
          <Select
            showSearch
            optionFilterProp="label"
            loading={dinhHuongLoading}
            placeholder="Chọn định hướng"
            options={(dinhHuong ?? []).map((d) => ({ value: d.id, label: dinhHuongLabel(d) }))}
          />
        </Form.Item>

        <Form.Item label="Mô tả" name="mo_ta">
          <TextArea maxLength={5000} showCount rows={4} />
        </Form.Item>

        <Form.Item
          label="File đính kèm"
          extra={
            topic?.tep_dinh_kem
              ? `Đã đính kèm: ${topic.tep_dinh_kem.ten_goc} — chọn file mới để thay.`
              : 'DOCX hoặc PDF, tối đa 20 MB (không bắt buộc).'
          }
        >
          <Upload
            accept=".docx,.pdf"
            maxCount={1}
            beforeUpload={(file) => {
              setTepDinhKem(file)
              return false
            }}
            onRemove={() => setTepDinhKem(null)}
            fileList={
              tepDinhKem
                ? [{ uid: '-1', name: tepDinhKem.name, status: 'done', size: tepDinhKem.size }]
                : []
            }
          >
            <Button>Chọn file</Button>
          </Upload>
        </Form.Item>
      </Form>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button onClick={() => navigate(-1)} disabled={isSaving}>
          Hủy
        </Button>
        <Button onClick={handleSaveDraft} disabled={noCohortOpen} loading={isSaving}>
          Lưu nháp
        </Button>
        <Button
          type="primary"
          onClick={handleAssign}
          disabled={noCohortOpen}
          loading={isSaving || checkTitleMutation.isPending}
        >
          {submitLabel}
        </Button>
      </div>
    </Card>
  )
}
