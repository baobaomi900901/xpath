export type RowItem = {
  key: number;
  id: number;
  name: string;
  department: string;
  city: string;
  status: 'active' | 'inactive' | 'pending';
  email: string;
  joinDate: string;
};

export const DEPARTMENTS = ['研发部', '产品部', '市场部', '销售部', '人事部'];
export const CITIES = ['北京', '上海', '广州', '深圳', '杭州'];
export const STATUSES: RowItem['status'][] = ['active', 'inactive', 'pending'];

export const STATUS_LABEL: Record<RowItem['status'], string> = {
  active: '在职',
  inactive: '离职',
  pending: '待入职',
};

export const STATUS_STYLE: Record<RowItem['status'], { background: string; color: string }> = {
  active: { background: '#f6ffed', color: '#389e0d' },
  inactive: { background: '#fafafa', color: '#595959' },
  pending: { background: '#fff7e6', color: '#d46b08' },
};

export const TABLE_COLUMNS = [
  { key: 'id', title: 'ID', width: '90px' },
  { key: 'name', title: '姓名', width: '140px' },
  { key: 'department', title: '部门', width: '140px' },
  { key: 'city', title: '城市', width: '120px' },
  { key: 'status', title: '状态', width: '120px' },
  { key: 'email', title: '邮箱', width: '1fr' },
  { key: 'joinDate', title: '入职日期', width: '140px' },
] as const;

export const GRID_TEMPLATE = TABLE_COLUMNS.map((col) => col.width).join(' ');

export function buildRows(total: number): RowItem[] {
  return Array.from({ length: total }, (_, index) => {
    const id = index + 1;
    const status = STATUSES[id % STATUSES.length];
    return {
      key: id,
      id,
      name: `用户${id}`,
      department: DEPARTMENTS[id % DEPARTMENTS.length],
      city: CITIES[id % CITIES.length],
      status,
      email: `user${id}@example.com`,
      joinDate: `2024-${String((id % 12) + 1).padStart(2, '0')}-${String((id % 28) + 1).padStart(2, '0')}`,
    };
  });
}
