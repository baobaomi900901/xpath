import { useMemo, useState, type CSSProperties, type FocusEvent, type ReactNode } from 'react';
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
} from 'antd';
import type { FormInstance, Rule } from 'antd/es/form';
import PageLayout from '../components/PageLayout';
import { randomId } from '../utils/random';

const HOBBY_OPTIONS = [
  { value: 'read', label: '阅读' },
  { value: 'sport', label: '运动' },
  { value: 'music', label: '音乐' },
  { value: 'travel', label: '旅行' },
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
    read: ids.hobbyRead,
    sport: ids.hobbySport,
    music: ids.hobbyMusic,
    travel: ids.hobbyTravel,
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
    read: ids.hobbyRead,
    sport: ids.hobbySport,
    music: ids.hobbyMusic,
    travel: ids.hobbyTravel,
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

function NativeGenderRadioGroup({ value = 'male', onChange, ids }: NativeGenderRadioGroupProps) {
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
  number?: number;
  date?: unknown;
  time?: unknown;
  search?: string;
  city?: string;
  gender?: string;
  hobbies?: string[];
  remark?: string;
  range?: number;
};

type NativeFormValues = {
  text?: string;
  password?: string;
  email?: string;
  number?: number;
  date?: string;
  time?: string;
  search?: string;
  city?: string;
  gender?: string;
  hobbies?: string[];
  remark?: string;
  range?: number;
};

const ANT_INITIAL_VALUES: AntFormValues = {
  text: '',
  password: '',
  email: '',
  number: 10,
  date: undefined,
  time: undefined,
  search: '',
  city: undefined,
  gender: 'male',
  hobbies: ['sport'],
  remark: '',
  range: 50,
};

const NATIVE_INITIAL_VALUES: NativeFormValues = {
  text: '',
  password: '',
  email: '',
  number: 10,
  date: '',
  time: '',
  search: '',
  city: '',
  gender: 'male',
  hobbies: ['sport'],
  remark: '',
  range: 50,
};

const RESULT_PLACEHOLDER = '填写表单后点击「提交」查看取值结果';

const FORM_LAYOUT = 'vertical' as const;

const FORM_ITEM_STYLE: CSSProperties = {
  marginBottom: 16,
};

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
      city: randomId(),
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
      submit: randomId('btn_native_'),
      reset: randomId('btn_native_'),
    }),
    [],
  );

  const handleAntSubmit = async () => {
    try {
      const values = await antForm.validateFields();
      setAntResult(JSON.stringify(values, null, 2));
    } catch {
      // 校验失败时 Form.Item 会展示错误信息
    }
  };

  const handleNativeSubmit = async () => {
    try {
      const values = await nativeForm.validateFields();
      setNativeResult(JSON.stringify(values, null, 2));
    } catch {
      // 校验失败时 Form.Item 会展示错误信息
    }
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
    options?: { antRules?: Rule[]; nativeRules?: Rule[] },
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
        <Form.Item label={label} name={name} rules={options?.nativeRules} style={FORM_ITEM_STYLE}>
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
          )}
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
          )}

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
          )}
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="禁用输入框" style={FORM_ITEM_STYLE}>
              <Input id={antIds.disabled} value="不可编辑" disabled />
            </Form.Item>
          )}
          native={(
            <Form.Item label="禁用输入框" style={FORM_ITEM_STYLE}>
              <input id={nativeIds.disabled} type="text" value="不可编辑" disabled style={NATIVE_DISABLED_STYLE} />
            </Form.Item>
          )}
        />
        <AlignedFormRow
          antForm={antForm}
          nativeForm={nativeForm}
          ant={(
            <Form.Item label="只读输入框" style={FORM_ITEM_STYLE}>
              <Input id={antIds.readonly} value="只读内容" readOnly />
            </Form.Item>
          )}
          native={(
            <Form.Item label="只读输入框" style={FORM_ITEM_STYLE}>
              <input id={nativeIds.readonly} type="text" value="只读内容" readOnly style={NATIVE_READONLY_STYLE} />
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
