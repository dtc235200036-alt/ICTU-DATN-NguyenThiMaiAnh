import { useEffect, useRef, useState } from 'react'
import { App as AntApp, Alert, Button, Card, Form, Input, Select, Tag } from 'antd'
import type { InputRef } from 'antd'
import { useNavigate, useParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useCohorts } from '../cohorts/api'
import ForbiddenPage from '../auth/ForbiddenPage'
import { LINH_VUC_OPTIONS } from './constants'
import TitleCheckAlert from './TitleCheckAlert'
import {
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
  linh_vuc?: string
  mo_ta?: string
}

/**
 * MH-06 (UC1.1): đề xuất đề tài mới ('/de-tai/de-xuat') hoặc sửa nháp
 * ('/de-tai/:id/sua'). Cùng một component cho cả hai chế độ — phân biệt qua
 * có/không có :id trên URL.
 */
export default function TopicFormPage() {
  const { id } = useParams()
  const editing = id !== undefined
  const topicId = editing ? Number(id) : undefined
  const navigate = useNavigate()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm<FormValues>()
  const titleInputRef = useRef<InputRef>(null)

  const { data: cohorts, isLoading: cohortsLoading } = useCohorts({ trang_thai: 'DANG_MO' })
  const { data: topic, isLoading: topicLoading, isFetched: topicFetched } = useTopic(topicId)

  const createMutation = useCreateTopic()
  const updateMutation = useUpdateTopic()
  const submitMutation = useSubmitTopic()
  const checkTitleMutation = useCheckTitle()

  // UC0.6/FR-DT-02: kết quả kiểm tra trùng tên tức thời (chưa lưu — bản lưu
  // chỉ xảy ra khi thật sự gửi đề xuất, ở service topics.py).
  const [checkResult, setCheckResult] = useState<TitleCheckResult | null>(null)
  const [lastCheckedTitle, setLastCheckedTitle] = useState<string | null>(null)
  const [acknowledged, setAcknowledged] = useState(false)

  useEffect(() => {
    if (editing && topic) {
      form.setFieldsValue({
        dot_do_an_id: topic.dot_do_an.id,
        ten_de_tai: topic.ten_de_tai,
        linh_vuc: topic.linh_vuc ?? undefined,
        mo_ta: topic.mo_ta ?? undefined,
      })
      setLastCheckedTitle(topic.ten_de_tai)
    }
  }, [editing, topic, form])

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

  const buildInput = (values: FormValues): TopicFormInput => ({
    dot_do_an_id: values.dot_do_an_id,
    ten_de_tai: values.ten_de_tai,
    linh_vuc: values.linh_vuc ?? null,
    mo_ta: values.mo_ta ?? null,
  })

  const isSaving =
    createMutation.isPending || updateMutation.isPending || submitMutation.isPending

  // Mọi lần đổi tên đề tài làm kết quả cũ (và xác nhận "vẫn gửi") hết hiệu lực
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
      message.success('Đã lưu nháp đề tài')
      if (savedId !== undefined) {
        navigate(`/de-tai/${savedId}`)
      }
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const doSubmitProposal = async (values: FormValues) => {
    try {
      let savedId = topicId
      if (editing && topicId !== undefined) {
        await updateMutation.mutateAsync({ id: topicId, input: buildInput(values) })
        await submitMutation.mutateAsync(topicId)
      } else {
        const created = await createMutation.mutateAsync({ ...buildInput(values), gui: true })
        savedId = created.id
      }
      message.success('Đã gửi đề xuất đề tài')
      if (savedId !== undefined) {
        navigate(`/de-tai/${savedId}`)
      }
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const handleSubmitProposal = async () => {
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

    await doSubmitProposal(values)
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
          message="Hiện không có đợt đồ án nào đang mở nhận đề xuất"
          style={{ marginBottom: 16 }}
        />
      )}
      <Form form={form} layout="vertical">
        <Form.Item
          label="Đợt đồ án"
          name="dot_do_an_id"
          extra="Chỉ hiển thị các đợt đang mở nhận đề xuất."
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
                Đã xác nhận gửi kèm cảnh báo
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

        <Form.Item label="Lĩnh vực" name="linh_vuc">
          <Select
            allowClear
            placeholder="Chọn lĩnh vực"
            options={LINH_VUC_OPTIONS.map((v) => ({ value: v, label: v }))}
          />
        </Form.Item>

        <Form.Item label="Mô tả" name="mo_ta">
          <TextArea maxLength={5000} showCount rows={5} />
        </Form.Item>
      </Form>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button onClick={handleSaveDraft} disabled={noCohortOpen} loading={isSaving}>
          Lưu nháp
        </Button>
        <Button
          type="primary"
          onClick={handleSubmitProposal}
          disabled={noCohortOpen}
          loading={isSaving || checkTitleMutation.isPending}
        >
          Gửi đề xuất
        </Button>
      </div>
    </Card>
  )
}
