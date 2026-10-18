import { List, Typography } from 'antd'

import type { CheckItem } from './api'

/** Các mục kiểm tra trước khi nộp lên/phê duyệt (tên file, định hướng, nội dung). */
export default function CheckList({ items }: { items: CheckItem[] }) {
  if (items.length === 0) return null
  return (
    <List
      size="small"
      bordered
      dataSource={items}
      renderItem={(item) => (
        <List.Item>
          <div style={{ display: 'flex', gap: 10 }}>
            <span style={{ color: item.dat ? '#52c41a' : '#ff4d4f', fontWeight: 600 }}>
              {item.dat ? '✓' : '✗'}
            </span>
            <div>
              <div style={{ fontWeight: 500 }}>{item.ten}</div>
              {item.chi_tiet && (
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {item.chi_tiet}
                </Typography.Text>
              )}
            </div>
          </div>
        </List.Item>
      )}
    />
  )
}
