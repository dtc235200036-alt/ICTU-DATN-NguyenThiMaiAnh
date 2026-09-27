import { Button, Result } from 'antd'
import { useNavigate } from 'react-router'

export default function ForbiddenPage() {
  const navigate = useNavigate()

  return (
    <Result
      status="403"
      title="403"
      subTitle="Bạn không có quyền truy cập trang này"
      extra={
        <Button type="primary" onClick={() => navigate('/tong-quan')}>
          Về trang tổng quan
        </Button>
      }
    />
  )
}
