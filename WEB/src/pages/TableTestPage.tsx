import { useMemo, useState } from 'react';
import { Alert, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import PageLayout from '../components/PageLayout';
import {
  STATUS_LABEL,
  buildRows,
  type RowItem,
} from '../utils/tableData';

const STATUS_COLOR: Record<RowItem['status'], string> = {
  active: 'green',
  inactive: 'default',
  pending: 'orange',
};

const columns: ColumnsType<RowItem> = [
  { title: 'ID', dataIndex: 'id', width: 90, sorter: (a, b) => a.id - b.id },
  { title: '姓名', dataIndex: 'name', width: 140 },
  { title: '部门', dataIndex: 'department', width: 140 },
  { title: '城市', dataIndex: 'city', width: 120 },
  {
    title: '状态',
    dataIndex: 'status',
    width: 120,
    render: (status: RowItem['status']) => <Tag color={STATUS_COLOR[status]}>{STATUS_LABEL[status]}</Tag>,
  },
  { title: '邮箱', dataIndex: 'email', ellipsis: true },
  { title: '入职日期', dataIndex: 'joinDate', width: 140 },
];

export default function TableTestPage() {
  const dataSource = useMemo(() => buildRows(1000), []);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

  return (
    <PageLayout title="表格测试" subtitle="Ant Design Table，7 列 × 1000 行" maxWidth={1400} inset={24}>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={`共 ${dataSource.length} 条数据，支持分页、排序与纵向滚动`}
      />

      <Table<RowItem>
        id="demo-table"
        rowKey="id"
        columns={columns}
        dataSource={dataSource}
        scroll={{ y: 560 }}
        tableLayout="fixed"
        style={{ width: '100%' }}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: dataSource.length,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: (total) => `共 ${total} 条`,
          onChange: (current, pageSize) => setPagination({ current, pageSize }),
        }}
      />

      <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
        当前页：第 {pagination.current} 页，每页 {pagination.pageSize} 条
      </Typography.Paragraph>
    </PageLayout>
  );
}
