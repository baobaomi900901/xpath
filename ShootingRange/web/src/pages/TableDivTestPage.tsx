import { useMemo, useState, type CSSProperties } from 'react';
import { Alert, Pagination, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import {
  GRID_TEMPLATE,
  STATUS_LABEL,
  STATUS_STYLE,
  TABLE_COLUMNS,
  buildRows,
  type RowItem,
} from '../utils/tableData';

const rowStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: GRID_TEMPLATE,
  alignItems: 'center',
  borderBottom: '1px solid #f0f0f0',
  minHeight: 48,
};

const cellStyle: CSSProperties = {
  padding: '12px 16px',
  fontSize: 14,
  color: '#1f2937',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const headerCellStyle: CSSProperties = {
  ...cellStyle,
  fontWeight: 600,
  color: '#334155',
  background: '#fafafa',
  borderBottom: '1px solid #f0f0f0',
};

function StatusBadge({ status }: { status: RowItem['status'] }) {
  const style = STATUS_STYLE[status];
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 4,
        fontSize: 12,
        background: style.background,
        color: style.color,
      }}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

export default function TableDivTestPage() {
  const dataSource = useMemo(() => buildRows(1000), []);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [sortAsc, setSortAsc] = useState(true);

  const sortedData = useMemo(() => {
    const copy = [...dataSource];
    copy.sort((a, b) => (sortAsc ? a.id - b.id : b.id - a.id));
    return copy;
  }, [dataSource, sortAsc]);

  const pageData = useMemo(() => {
    const start = (pagination.current - 1) * pagination.pageSize;
    return sortedData.slice(start, start + pagination.pageSize);
  }, [sortedData, pagination]);

  return (
    <PageLayout
      title="表格测试(div一把梭)"
      subtitle="纯 div 实现，7 列 × 1000 行，内容与 Ant Design Table 一致"
      maxWidth={1400}
      inset={24}
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={`共 ${dataSource.length} 条数据，支持分页、ID 排序与纵向滚动`}
      />

      <div
        id="demo-div-table"
        style={{
          width: '100%',
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          overflow: 'hidden',
          background: '#fff',
        }}
      >
        <div style={{ ...rowStyle, borderBottom: '1px solid #f0f0f0' }}>
          {TABLE_COLUMNS.map((column) => (
            <div
              key={column.key}
              style={{
                ...headerCellStyle,
                cursor: column.key === 'id' ? 'pointer' : 'default',
                userSelect: 'none',
              }}
              onClick={column.key === 'id' ? () => setSortAsc((value) => !value) : undefined}
            >
              {column.title}
              {column.key === 'id' ? (sortAsc ? ' ↑' : ' ↓') : ''}
            </div>
          ))}
        </div>

        <div style={{ maxHeight: 560, overflowY: 'auto' }}>
          {pageData.map((row) => (
            <div key={row.id} id={`div-table-row-${row.id}`} style={rowStyle}>
              <div style={cellStyle}>{row.id}</div>
              <div style={cellStyle}>{row.name}</div>
              <div style={cellStyle}>{row.department}</div>
              <div style={cellStyle}>{row.city}</div>
              <div style={cellStyle}>
                <StatusBadge status={row.status} />
              </div>
              <div style={cellStyle} title={row.email}>
                <a href={`mailto:${row.email}`} style={{ color: '#1677ff' }}>
                  {row.email}
                </a>
              </div>
              <div style={cellStyle}>{row.joinDate}</div>
            </div>
          ))}
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            padding: '16px',
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Pagination
            current={pagination.current}
            pageSize={pagination.pageSize}
            total={dataSource.length}
            showSizeChanger
            showQuickJumper
            pageSizeOptions={['10', '20', '50', '100']}
            showTotal={(total) => `共 ${total} 条`}
            onChange={(current, pageSize) => setPagination({ current, pageSize })}
          />
        </div>
      </div>

      <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
        当前页：第 {pagination.current} 页，每页 {pagination.pageSize} 条
      </Typography.Paragraph>
    </PageLayout>
  );
}
