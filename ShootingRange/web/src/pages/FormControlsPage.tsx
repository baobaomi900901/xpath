import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type FocusEvent,
  type ReactNode,
} from 'react';
import {
  Alert,
  Button,
  Checkbox,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Radio,
  Select,
  Slider,
  Space,
  TimePicker,
  Typography,
  message,
} from 'antd';
import type { FormInstance, Rule } from 'antd/es/form';
import PageLayout from '../components/PageLayout';
import { randomId } from '../utils/random';

const HOBBY_OPTIONS = [
  { value: '阅读', label: '阅读' },
  { value: '运动', label: '运动' },
  { value: '音乐', label: '音乐' },
  { value: '旅行', label: '旅行' },
];

const HOBBY_VALUES = HOBBY_OPTIONS.map((item) => item.value);

const CITY_OPTIONS = [
  { value: 'beijing', label: '北京' },
  { value: 'shanghai', label: '上海' },
  { value: 'guangzhou', label: '广州' },
  { value: 'shenzhen', label: '深圳' },
];

const NATIVE_INPUT_STYLE: CSSProperties = {
  width: '100%',
  height: 32,
  padding: '4px 11px',
  fontSize: 14,
  lineHeight: '22px',
  borderRadius: 6,
  border: '1px solid #d9d9d9',
  boxSizing: 'border-box',
  outline: 'none',
  transition: 'all 0.2s',
  background: '#fff',
  color: 'rgba(0, 0, 0, 0.88)',
};

const NATIVE_TEXTAREA_STYLE: CSSProperties = {
  ...NATIVE_INPUT_STYLE,
  height: 'auto',
  minHeight: 96,
  padding: '4px 11px',
  resize: 'vertical',
};

const NATIVE_DISABLED_STYLE: CSSProperties = {
  ...NATIVE_INPUT_STYLE,
  background: 'rgba(0, 0, 0, 0.04)',
  color: 'rgba(0, 0, 0, 0.25)',
  cursor: 'not-allowed',
};

const NATIVE_READONLY_STYLE: CSSProperties = {
  ...NATIVE_INPUT_STYLE,
  background: '#fff',
  cursor: 'default',
};

const GRID_STYLE: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'minmax(0, 1fr) 1px minmax(0, 1fr)',
  columnGap: 24,
  alignItems: 'start',
};

const DIVIDER_STYLE: CSSProperties = {
  width: 1,
  background: '#EEE',
  alignSelf: 'stretch',
  minHeight: '100%',
};

function nativeFocusStyle(event: FocusEvent<HTMLElement>) {
  event.currentTarget.style.borderColor = '#4096ff';
  event.currentTarget.style.boxShadow = '0 0 0 2px rgba(5, 145, 255, 0.1)';
}

function nativeBlurStyle(event: FocusEvent<HTMLElement>) {
  event.currentTarget.style.borderColor = '#d9d9d9';
  event.currentTarget.style.boxShadow = 'none';
}

type HobbyCheckboxGroupProps = {
  value?: string[];
  onChange?: (value: string[]) => void;
  ids: {
    hobbyAll: string;
    hobbyRead: string;
    hobbySport: string;
    hobbyMusic: string;
    hobbyTravel: string;
  };
};

const HOBBY_SELECT_ALL_ROW_STYLE: CSSProperties = {
  marginBottom: 8,
  minHeight: 22,
  display: 'flex',
  alignItems: 'center',
};

const HOBBY_OPTION_ROW_STYLE: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  columnGap: 16,
  rowGap: 8,
  alignItems: 'center',
};

const NATIVE_CHECKBOX_STYLE: CSSProperties = {
  width: 16,
  height: 16,
  margin: 0,
  flexShrink: 0,
  accentColor: '#1677ff',
};

const NATIVE_CHECKBOX_LABEL_STYLE: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 8,
  cursor: 'pointer',
  fontSize: 14,
  lineHeight: '22px',
  color: 'rgba(0, 0, 0, 0.88)',
};

function HobbyCheckboxGroup({ value = [], onChange, ids }: HobbyCheckboxGroupProps) {
  const selected = value ?? [];
  const allChecked = selected.length === HOBBY_VALUES.length;
  const indeterminate = selected.length > 0 && selected.length < HOBBY_VALUES.length;

  const hobbyIdMap: Record<string, string> = {
    阅读: ids.hobbyRead,
    运动: ids.hobbySport,
    音乐: ids.hobbyMusic,
    旅行: ids.hobbyTravel,
  };

  return (
    <div>
      <div style={HOBBY_SELECT_ALL_ROW_STYLE}>
        <Checkbox
          id={ids.hobbyAll}
          indeterminate={indeterminate}
          checked={allChecked}
          onChange={(event) => onChange?.(event.target.checked ? [...HOBBY_VALUES] : [])}
        >
          全选
        </Checkbox>
      </div>
      <Checkbox.Group
        value={selected}
        onChange={(checked) => onChange?.(checked as string[])}
        style={HOBBY_OPTION_ROW_STYLE}
      >
        {HOBBY_OPTIONS.map((item) => (
          <Checkbox key={item.value} id={hobbyIdMap[item.value]} value={item.value}>
            {item.label}
          </Checkbox>
        ))}
      </Checkbox.Group>
    </div>
  );
}

function NativeHobbyCheckboxGroup({ value = [], onChange, ids }: HobbyCheckboxGroupProps) {
  const selected = value ?? [];
  const allChecked = selected.length === HOBBY_VALUES.length;
  const indeterminate = selected.length > 0 && selected.length < HOBBY_VALUES.length;

  const hobbyIdMap: Record<string, string> = {
    阅读: ids.hobbyRead,
    运动: ids.hobbySport,
    音乐: ids.hobbyMusic,
    旅行: ids.hobbyTravel,
  };

  const toggle = (optionValue: string, checked: boolean) => {
    onChange?.(checked ? [...selected, optionValue] : selected.filter((item) => item !== optionValue));
  };

  return (
    <div>
      <div style={HOBBY_SELECT_ALL_ROW_STYLE}>
        <label htmlFor={ids.hobbyAll} style={NATIVE_CHECKBOX_LABEL_STYLE}>
          <input
            id={ids.hobbyAll}
            type="checkbox"
            style={NATIVE_CHECKBOX_STYLE}
            checked={allChecked}
            ref={(element) => {
              if (element) element.indeterminate = indeterminate;
            }}
            onChange={(event) => onChange?.(event.target.checked ? [...HOBBY_VALUES] : [])}
          />
          全选
        </label>
      </div>
      <div style={HOBBY_OPTION_ROW_STYLE}>
        {HOBBY_OPTIONS.map((item) => (
          <label
            key={item.value}
            htmlFor={hobbyIdMap[item.value]}
            style={NATIVE_CHECKBOX_LABEL_STYLE}
          >
            <input
              id={hobbyIdMap[item.value]}
              type="checkbox"
              style={NATIVE_CHECKBOX_STYLE}
              value={item.value}
              checked={selected.includes(item.value)}
              onChange={(event) => toggle(item.value, event.target.checked)}
            />
            {item.label}
          </label>
        ))}
      </div>
    </div>
  );
}

type NativeGenderRadioGroupProps = {
  value?: string;
  onChange?: (value: string) => void;
  ids: {
    male: string;
    female: string;
    other: string;
  };
};

type NativeMultiSelectProps = {
  id: string;
  value?: string[];
  onChange?: (value: string[]) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
};

const NATIVE_MULTI_SHELL_STYLE: CSSProperties = {
  ...NATIVE_INPUT_STYLE,
  position: 'relative',
  height: 'auto',
  minHeight: 32,
  display: 'flex',
  flexWrap: 'wrap',
  alignItems: 'center',
  gap: 4,
  padding: '3px 7px',
  cursor: 'text',
};

const NATIVE_MULTI_TAG_STYLE: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
  height: 24,
  padding: '0 7px',
  fontSize: 12,
  lineHeight: '22px',
  borderRadius: 4,
  background: 'rgba(0, 0, 0, 0.06)',
  color: 'rgba(0, 0, 0, 0.88)',
};

const NATIVE_MULTI_INPUT_STYLE: CSSProperties = {
  flex: 1,
  minWidth: 80,
  height: 24,
  margin: 0,
  padding: 0,
  border: 'none',
  outline: 'none',
  background: 'transparent',
  fontSize: 14,
  lineHeight: '24px',
  color: 'rgba(0, 0, 0, 0.88)',
};

const NATIVE_MULTI_DROPDOWN_STYLE: CSSProperties = {
  position: 'absolute',
  top: 'calc(100% + 4px)',
  left: 0,
  right: 0,
  zIndex: 20,
  maxHeight: 180,
  overflowY: 'auto',
  margin: 0,
  padding: '4px 0',
  listStyle: 'none',
  background: '#fff',
  border: '1px solid #d9d9d9',
  borderRadius: 6,
  boxShadow: '0 6px 16px rgba(0, 0, 0, 0.08)',
};

function NativeMultiSelect({
  id,
  value = [],
  onChange,
  options,
  placeholder = '请选择城市（可多选）',
}: NativeMultiSelectProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [focused, setFocused] = useState(false);

  const selectedSet = useMemo(() => new Set(value), [value]);
  const labelMap = useMemo(
    () => new Map(options.map((item) => [item.value, item.label])),
    [options],
  );
  const filtered = useMemo(() => {
    const key = keyword.trim().toLowerCase();
    if (!key) return options;
    return options.filter((item) => item.label.toLowerCase().includes(key) || item.value.toLowerCase().includes(key));
  }, [keyword, options]);

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setKeyword('');
      }
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [open]);

  const toggle = (optionValue: string) => {
    if (selectedSet.has(optionValue)) {
      onChange?.(value.filter((item) => item !== optionValue));
    } else {
      onChange?.([...value, optionValue]);
    }
    setKeyword('');
  };

  const shellStyle: CSSProperties = {
    ...NATIVE_MULTI_SHELL_STYLE,
    ...(focused
      ? {
          borderColor: '#4096ff',
          boxShadow: '0 0 0 2px rgba(5, 145, 255, 0.1)',
        }
      : null),
  };

  return (
    <div
      ref={rootRef}
      style={shellStyle}
      onMouseDown={(event) => {
        if ((event.target as HTMLElement).closest('button')) return;
        setOpen(true);
      }}
    >
      {value.map((item) => (
        <span key={item} style={NATIVE_MULTI_TAG_STYLE}>
          {labelMap.get(item) ?? item}
          <button
            type="button"
            aria-label={`移除 ${labelMap.get(item) ?? item}`}
            style={{
              border: 'none',
              background: 'transparent',
              padding: 0,
              margin: 0,
              cursor: 'pointer',
              lineHeight: 1,
              color: 'rgba(0, 0, 0, 0.45)',
            }}
            onClick={(event) => {
              event.stopPropagation();
              onChange?.(value.filter((current) => current !== item));
            }}
          >
            ×
          </button>
        </span>
      ))}
      <input
        id={id}
        type="text"
        value={keyword}
        placeholder={value.length === 0 ? placeholder : ''}
        style={NATIVE_MULTI_INPUT_STYLE}
        autoComplete="off"
        onFocus={() => {
          setFocused(true);
          setOpen(true);
        }}
        onBlur={() => setFocused(false)}
        onChange={(event) => {
          setKeyword(event.target.value);
          setOpen(true);
        }}
        onKeyDown={(event) => {
          if (event.key === 'Backspace' && !keyword && value.length > 0) {
            onChange?.(value.slice(0, -1));
          }
          if (event.key === 'Escape') {
            setOpen(false);
            setKeyword('');
          }
        }}
      />
      {open && (
        <ul style={NATIVE_MULTI_DROPDOWN_STYLE} role="listbox" aria-multiselectable>
          {filtered.length === 0 ? (
            <li style={{ padding: '5px 12px', color: 'rgba(0, 0, 0, 0.25)' }}>无匹配选项</li>
          ) : (
            filtered.map((item) => {
              const selected = selectedSet.has(item.value);
              return (
                <li
                  key={item.value}
                  role="option"
                  aria-selected={selected}
                  style={{
                    padding: '5px 12px',
                    cursor: 'pointer',
                    background: selected ? '#e6f4ff' : 'transparent',
                    color: 'rgba(0, 0, 0, 0.88)',
                  }}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    toggle(item.value);
                  }}
                >
                  {item.label}
                </li>
              );
            })
          )}
        </ul>
      )}
    </div>
  );
}

function NativeGenderRadioGroup({ value, onChange, ids }: NativeGenderRadioGroupProps) {
  const options = [
    { value: 'male', label: '男', id: ids.male },
    { value: 'female', label: '女', id: ids.female },
    { value: 'other', label: '其他', id: ids.other },
  ];

  return (
    <div style={{ minHeight: 32, lineHeight: '32px', fontSize: 14 }}>
      {options.map((item) => (
        <label key={item.value} htmlFor={item.id} style={{ marginRight: 16, cursor: 'pointer' }}>
          <input
            id={item.id}
            type="radio"
            name="native-gender"
            value={item.value}
            checked={value === item.value}
            onChange={() => onChange?.(item.value)}
          />
          {' '}{item.label}
        </label>
      ))}
    </div>
  );
}

type AntFormValues = {
  text?: string;
  password?: string;
  email?: string;
  number?: number | null;
  date?: unknown;
  time?: unknown;
  search?: string;
  city?: string;
  cities?: string[];
  gender?: string;
  hobbies?: string[];
  remark?: string;
  range?: number | null;
  disabled?: string;
  readonly?: string;
};

type NativeFormValues = {
  text?: string;
  password?: string;
  email?: string;
  number?: number | null;
  date?: string;
  time?: string;
  search?: string;
  city?: string;
  cities?: string[];
  gender?: string;
  hobbies?: string[];
  remark?: string;
  range?: number | null;
  disabled?: string;
  readonly?: string;
};

const DISABLED_FIELD_VALUE = '不可编辑';
const READONLY_FIELD_VALUE = '只读内容';

const FORM_SNAPSHOT_KEYS = [
  'text',
  'password',
  'email',
  'number',
  'date',
  'time',
  'search',
  'disabled',
  'city',
  'cities',
  'gender',
  'hobbies',
  'remark',
  'range',
  'readonly',
] as const;

const ANT_INITIAL_VALUES: AntFormValues = {
  text: '',
  password: '',
  email: '',
  number: null,
  date: undefined,
  time: undefined,
  search: '',
  city: undefined,
  cities: [],
  gender: undefined,
  hobbies: [],
  remark: '',
  range: 0,
  disabled: DISABLED_FIELD_VALUE,
  readonly: READONLY_FIELD_VALUE,
};

const NATIVE_INITIAL_VALUES: NativeFormValues = {
  text: '',
  password: '',
  email: '',
  number: null,
  date: '',
  time: '',
  search: '',
  city: '',
  cities: [],
  gender: undefined,
  hobbies: [],
  remark: '',
  range: 0,
  disabled: DISABLED_FIELD_VALUE,
  readonly: READONLY_FIELD_VALUE,
};

const RESULT_PLACEHOLDER = '填写表单后点击「提交」查看取值结果';

const FORM_LAYOUT = 'vertical' as const;

const FORM_ITEM_STYLE: CSSProperties = {
  marginBottom: 16,
};

function buildFormSnapshot(
  form: FormInstance,
  initialValues: Record<string, unknown>,
): Record<string, unknown> {
  const raw = form.getFieldsValue(true) as Record<string, unknown>;
  const merged: Record<string, unknown> = {
    ...initialValues,
    ...raw,
    disabled: DISABLED_FIELD_VALUE,
    readonly: READONLY_FIELD_VALUE,
  };
  const ordered: Record<string, unknown> = {};
  for (const key of FORM_SNAPSHOT_KEYS) {
    ordered[key] = merged[key] ?? null;
  }
  return ordered;
}

function serializeFormValues(values: Record<string, unknown>) {
  return JSON.stringify(
    values,
    (_key, value) => {
      if (value && typeof value === 'object' && typeof (value as { format?: unknown }).format === 'function') {
        return (value as { format: (pattern: string) => string }).format('YYYY-MM-DD HH:mm:ss');
      }
      return value ?? null;
    },
    2,
  );
}

async function copyFormJson(values: Record<string, unknown>, label: string) {
  const text = serializeFormValues(values);
  try {
    await navigator.clipboard.writeText(text);
    message.success(`${label} 表单 JSON 已复制到剪贴板`);
  } catch {
    message.error('复制失败, 请检查浏览器剪贴板权限');
  }
  return text;
}

function FormSectionTitle({ title }: { title: string }) {
  return (
    <>
      <Typography.Title level={5} style={{ margin: '16px 0 8px' }}>
        {title}
      </Typography.Title>
      <div style={DIVIDER_STYLE} aria-hidden />
      <Typography.Title level={5} style={{ margin: '16px 0 8px' }}>
        {title}
      </Typography.Title>
    </>
  );
}

function AlignedFormRow({
  ant,
  native,
  antForm,
  nativeForm,
}: {
  ant: ReactNode;
  native: ReactNode;
  antForm: FormInstance<AntFormValues>;
  nativeForm: FormInstance<NativeFormValues>;
}) {
  return (
    <>
      <Form form={antForm} component={false} layout={FORM_LAYOUT}>{ant}</Form>
      <div style={DIVIDER_STYLE} aria-hidden />
      <Form form={nativeForm} component={false} layout={FORM_LAYOUT}>{native}</Form>
    </>
  );
}

function nativeInputProps(onFocus = nativeFocusStyle, onBlur = nativeBlurStyle) {
  return { onFocus, onBlur };
}

export default function FormControlsPage() {
  const [antForm] = Form.useForm<AntFormValues>();
  const [nativeForm] = Form.useForm<NativeFormValues>();
  const [antResult, setAntResult] = useState(RESULT_PLACEHOLDER);
  const [nativeResult, setNativeResult] = useState(RESULT_PLACEHOLDER);

  const antIds = useMemo(
    () => ({
      text: randomId(),
      password: randomId(),
      email: randomId(),
      number: randomId(),
      date: randomId(),
      time: randomId(),
      search: randomId(),
      city: randomId(),
      cities: randomId(),
      genderMale: randomId(),
      genderFemale: randomId(),
      genderOther: randomId(),
      hobbyAll: randomId(),
      hobbyRead: randomId(),
      hobbySport: randomId(),
      hobbyMusic: randomId(),
      hobbyTravel: randomId(),
      remark: randomId(),
      range: randomId(),
      disabled: randomId(),
      readonly: randomId(),
      submit: randomId('btn_ant_'),
      reset: randomId('btn_ant_'),
    }),
    [],
  );

  const nativeIds = useMemo(
    () => ({
      text: randomId(),
      password: randomId(),
      email: randomId(),
      number: randomId(),
      date: randomId(),
      time: randomId(),
      search: randomId(),
      city: 'form-controls-native-city',
      cities: 'form-controls-native-cities',
      genderMale: randomId(),
      genderFemale: randomId(),
      genderOther: randomId(),
      hobbyAll: randomId(),
      hobbyRead: randomId(),
      hobbySport: randomId(),
      hobbyMusic: randomId(),
      hobbyTravel: randomId(),
      remark: randomId(),
      range: randomId(),
      disabled: randomId(),
      readonly: randomId(),
      submit: 'form-controls-native-submit',
      reset: 'form-controls-native-reset',
    }),
    [],
  );

  const handleAntSubmit = async () => {
    try {
      await antForm.validateFields();
    } catch {
      // 校验失败仍导出完整快照；错误信息由 Form.Item 展示
    }
    const values = buildFormSnapshot(antForm, ANT_INITIAL_VALUES as Record<string, unknown>);
    const text = await copyFormJson(values, 'Ant Design');
    setAntResult(text);
  };

  const handleNativeSubmit = async () => {
    try {
      await nativeForm.validateFields();
    } catch {
      // 校验失败仍导出完整快照；错误信息由 Form.Item 展示
    }
    const values = buildFormSnapshot(nativeForm, NATIVE_INITIAL_VALUES as Record<string, unknown>);
    const text = await copyFormJson(values, '原生 HTML');
    setNativeResult(text);
  };

  const emailRules: Rule[] = [
    {
      validator: async (_, value) => {
        if (!value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value))) {
          return;
        }
        throw new Error('请输入有效的邮箱地址');
      },
    },
  ];

  const handleAntReset = () => {
    antForm.resetFields();
    setAntResult(RESULT_PLACEHOLDER);
  };

  const handleNativeReset = () => {
    nativeForm.resetFields();
    setNativeResult(RESULT_PLACEHOLDER);
  };

  const hobbyAntIds = {
    hobbyAll: antIds.hobbyAll,
    hobbyRead: antIds.hobbyRead,
    hobbySport: antIds.hobbySport,
    hobbyMusic: antIds.hobbyMusic,
    hobbyTravel: antIds.hobbyTravel,
  };

  const hobbyNativeIds = {
    hobbyAll: nativeIds.hobbyAll,
    hobbyRead: nativeIds.hobbyRead,
    hobbySport: nativeIds.hobbySport,
    hobbyMusic: nativeIds.hobbyMusic,
    hobbyTravel: nativeIds.hobbyTravel,
  };

  const renderItem = (
    label: string,
    name: keyof AntFormValues & keyof NativeFormValues,
    antControl: ReactNode,
    nativeControl: ReactNode,
    options?: {
      antRules?: Rule[];
      nativeRules?: Rule[];
      nativeLabel?: string;
      nativeGetValueFromEvent?: (event: { target: { value: string } }) => unknown;
    },
  ) => (
    <AlignedFormRow
      key={String(name)}
      antForm={antForm}
      nativeForm={nativeForm}
      ant={(
        <Form.Item label={label} name={name} rules={options?.antRules} style={FORM_ITEM_STYLE}>
          {antControl}
        </Form.Item>
      )}
      native={(
        <Form.Item
          label={options?.nativeLabel ?? label}
          name={name}
          rules={options?.nativeRules}
          getValueFromEvent={options?.nativeGetValueFromEvent}
          style={FORM_ITEM_STYLE}
        >
          {nativeControl}
        </Form.Item>
      )}
    />
  );

  return (
    <PageLayout
      title="表单控件测试"
      subtitle="左侧 Ant Design 表单, 右侧原生 HTML 表单, 控件一一对齐"
      fullWidth
      inset={24}
    >
      <Alert
        type="warning"
        showIcon
        style={{ marginBottom: 20 }}
        message="每次刷新页面, 所有控件的 id 都会随机变化; label 文字固定, 可作为锚点定位"
      />

      <Form form={antForm} component={false} layout={FORM_LAYOUT} initialValues={ANT_INITIAL_VALUES} />
      <Form form={nativeForm} component={false} layout={FORM_LAYOUT} initialValues={NATIVE_INITIAL_VALUES} />

      <div style={GRID_STYLE}>
        <Typography.Title level={5} style={{ marginTop: 0, marginBottom: 0 }}>
          Ant Design 表单
        </Typography.Title>
        <div style={DIVIDER_STYLE} aria-hidden />
        <Typography.Title level={5} style={{ marginTop: 0, marginBottom: 0 }}>
          原生 HTML 表单
        </Typography.Title>

        <FormSectionTitle title="输入框" />
        {renderItem('文本输入框', 'text',
          <Input id={antIds.text} placeholder="请输入文本" />,
          <input id={nativeIds.text} type="text" placeholder="请输入文本" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          )}
        {renderItem('密码输入框', 'password',
          <Input.Password id={antIds.password} placeholder="请输入密码" />,
          <input id={nativeIds.password} type="password" placeholder="请输入密码" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          )}
        {renderItem('邮箱输入框', 'email',
          <Input id={antIds.email} placeholder="user@example.com" />,
          <input id={nativeIds.email} type="email" placeholder="user@example.com" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          { antRules: emailRules, nativeRules: emailRules })}
        {renderItem('数字输入框', 'number',
          <InputNumber id={antIds.number} min={0} max={100} style={{ width: '100%' }} />,
          <input id={nativeIds.number} type="number" min={0} max={100} style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          {
            nativeGetValueFromEvent: (event: { target: { value: string } }) => {
              const next = event.target.value;
              return next === '' ? null : Number(next);
            },
          })}
        {renderItem('日期选择', 'date',
          <DatePicker id={antIds.date} style={{ width: '100%' }} />,
          <input id={nativeIds.date} type="date" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          )}
        {renderItem('时间选择', 'time',
          <TimePicker id={antIds.time} style={{ width: '100%' }} />,
          <input id={nativeIds.time} type="time" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          )}
        {renderItem('搜索框', 'search',
          <Input.Search id={antIds.search} placeholder="搜索关键词" />,
          <input id={nativeIds.search} type="search" placeholder="搜索关键词" style={NATIVE_INPUT_STYLE} {...nativeInputProps()} />,
          )}
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="禁用输入框" name="disabled" style={FORM_ITEM_STYLE}>
              <Input id={antIds.disabled} disabled />
            </Form.Item>
          )}
          native={(
            <Form.Item label="禁用输入框" name="disabled" style={FORM_ITEM_STYLE}>
              <input id={nativeIds.disabled} type="text" disabled style={NATIVE_DISABLED_STYLE} />
            </Form.Item>
          )}
        />

        <FormSectionTitle title="下拉选择" />
        {renderItem('城市', 'city',
          <Select id={antIds.city} placeholder="请选择城市" options={CITY_OPTIONS} />,
          (
            <select id={nativeIds.city} style={NATIVE_INPUT_STYLE} {...nativeInputProps()}>
              <option value="">请选择城市</option>
              {CITY_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          ),
          { nativeLabel: '城市(暂时id不会变动)' })}
        {renderItem('城市多选', 'cities',
          <Select
            id={antIds.cities}
            mode="multiple"
            allowClear
            placeholder="请选择城市（可多选）"
            options={CITY_OPTIONS}
          />,
          <NativeMultiSelect id={nativeIds.cities} options={CITY_OPTIONS} />,
          { nativeLabel: '城市多选(暂时id不会变动)' })}

        <FormSectionTitle title="单选框" />
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="性别" name="gender" style={FORM_ITEM_STYLE}>
              <Radio.Group>
                <Radio id={antIds.genderMale} value="male">男</Radio>
                <Radio id={antIds.genderFemale} value="female">女</Radio>
                <Radio id={antIds.genderOther} value="other">其他</Radio>
              </Radio.Group>
            </Form.Item>
          )}
          native={(
            <Form.Item label="性别" name="gender" style={FORM_ITEM_STYLE}>
              <NativeGenderRadioGroup
                ids={{
                  male: nativeIds.genderMale,
                  female: nativeIds.genderFemale,
                  other: nativeIds.genderOther,
                }}
              />
            </Form.Item>
          )}
        />

        <FormSectionTitle title="多选框" />
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="兴趣爱好" name="hobbies" style={FORM_ITEM_STYLE}>
              <HobbyCheckboxGroup ids={hobbyAntIds} />
            </Form.Item>
          )}
          native={(
            <Form.Item label="兴趣爱好" name="hobbies" style={FORM_ITEM_STYLE}>
              <NativeHobbyCheckboxGroup ids={hobbyNativeIds} />
            </Form.Item>
          )}
        />

        <FormSectionTitle title="文本域" />
        {renderItem('备注', 'remark',
          <Input.TextArea id={antIds.remark} placeholder="请输入备注信息" rows={4} />,
          <textarea id={nativeIds.remark} placeholder="请输入备注信息" rows={4} style={NATIVE_TEXTAREA_STYLE} {...nativeInputProps()} />,
          )}

        <FormSectionTitle title="其他控件" />
        {renderItem('滑块', 'range',
          <Slider id={antIds.range} />,
          <input id={nativeIds.range} type="range" min={0} max={100} style={{ width: '100%', marginTop: 12 }} />,
          {
            nativeGetValueFromEvent: (event: { target: { value: string } }) => Number(event.target.value),
          })}
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="只读输入框" name="readonly" style={FORM_ITEM_STYLE}>
              <Input id={antIds.readonly} readOnly />
            </Form.Item>
          )}
          native={(
            <Form.Item label="只读输入框" name="readonly" style={FORM_ITEM_STYLE}>
              <input id={nativeIds.readonly} type="text" readOnly style={NATIVE_READONLY_STYLE} />
            </Form.Item>
          )}
        />

        <div>
          <Space>
            <Button id={antIds.submit} type="primary" onClick={handleAntSubmit}>提交</Button>
            <Button id={antIds.reset} onClick={handleAntReset}>重置</Button>
          </Space>
        </div>
        <div style={DIVIDER_STYLE} aria-hidden />
        <div>
          <Space>
            <Button id={nativeIds.submit} type="primary" onClick={handleNativeSubmit}>提交</Button>
            <Button id={nativeIds.reset} onClick={handleNativeReset}>重置</Button>
          </Space>
        </div>

        <Typography.Paragraph
          id="ant-result"
          style={{ marginTop: 20, padding: 12, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap', minHeight: 80 }}
        >
          {antResult}
        </Typography.Paragraph>
        <div style={DIVIDER_STYLE} aria-hidden />
        <Typography.Paragraph
          id="native-result"
          style={{ marginTop: 20, padding: 12, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap', minHeight: 80 }}
        >
          {nativeResult}
        </Typography.Paragraph>
      </div>
    </PageLayout>
  );
}
