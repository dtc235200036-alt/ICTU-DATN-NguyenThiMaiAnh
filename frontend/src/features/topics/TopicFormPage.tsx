import { useEffect, useRef } from 'react'
import { App as AntApp, Alert, Button, Card, Form, Input, Select } from 'antd'
import type { InputRef } from 'antd'
import { useNavigate, useParams } from 'react-router'

import { getErrorMessage } from '../../api/client'
import { useCohorts } from '../cohorts/api'
import ForbiddenPage from '../auth/ForbiddenPage'
import { LINH_VUC_OPTIONS } from './constants'
import { useCreateTopic, useSubmitTopic, useTopic, useUpdateTopic } from './api'
import type { TopicFormInput } from './api'

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

  useEffect(() => {
    if (editing && topic) {
      form.setFieldsValue({
        dot_do_an_id: topic.dot_do_an.id,
        ten_de_tai: topic.ten_de_tai,
        linh_vuc: topic.linh_vuc ?? undefined,
        mo_ta: topic.mo_ta ?? undefined,
      })
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

  const handleSubmitProposal = async () => {
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
          <Input ref={titleInputRef} maxLength={255} />
        </Form.Item>

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
          loading={isSaving}
        >
          Gửi đề xuất
        </Button>
      </div>
    </Card>
  )
}
