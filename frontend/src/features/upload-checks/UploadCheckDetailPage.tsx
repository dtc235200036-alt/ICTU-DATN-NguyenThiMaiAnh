import { Alert, Card, Empty, Skeleton } from 'antd'
import { Link, useParams } from 'react-router'

import { CheckResultView } from '../documents/CheckDetailPage'
import { useUploadCheck } from './api'

/** 0020: kết quả kiểm tra một tệp tải lên — cùng giao diện với kết quả tài liệu đã nộp. */
export default function UploadCheckDetailPage() {
  const id = Number(useParams<{ ketQuaId: string }>().ketQuaId)
  const { data, isLoading } = useUploadCheck(id)

  if (isLoading) {
    return (
      <Card>
        <Skeleton active />
      </Card>
    )
  }
  if (!data) {
    return (
      <Card>
        <Empty description="Không tìm thấy kết quả kiểm tra" />
      </Card>
    )
  }
  if (data.trang_thai === 'LOI') {
    return (
      <Card>
        <Alert
          type="error"
          showIcon
          message={`Kiểm tra "${data.ten_tep}" không thành công`}
          description={
            <>
              Dịch vụ AI không phản hồi hoặc quá thời gian. Hãy{' '}
              <Link to="/kiem-tra-dao-van">tải tệp lên lại</Link>.
            </>
          }
        />
      </Card>
    )
  }
  return <CheckResultView data={data} subtitle={data.ten_tep} loaiTaiLieu="Tệp tải lên" />
}
