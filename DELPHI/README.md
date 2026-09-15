# Delphi VCL UIA 靶场

这是一个面向 Delphi 2010 的无 DFM VCL 示例工程，用于模拟真实 Delphi/VCL 程序的 UIA 树形结构。

## 目标结构

```text
TMainForm
└─ MDIClient
   └─ TLayoutForm
      └─ TLayoutPanel
         └─ TPageControl
            └─ TTabSheet
               └─ TfrmETFDate
                  └─ TRzPanel（本工程用兼容 TPanel 模拟）
                     └─ THs08ComboBox
```

## 功能

- MDI 主窗体和 `TPageControl/TTabSheet`
- 用户信息表单、VCL `THs08ComboBox` 单选下拉框
- 原生“文件/编辑”顶部菜单
- 表单页动态 `TPopupMenu` 操作菜单
- 输入框右键菜单（撤销、剪切、复制、粘贴、全选）
- 表格页 `TListView`
- 拖拽测试、复制状态、销毁/重建 `drag-target`

`THs08ComboBox`、`TRzPanel` 是兼容类。没有安装 Raize Components 时，工程仍可使用标准 VCL 控件编译；它们的真实第三方 Provider 行为不等同于生产程序。

## Delphi 2010 编译

1. 在安装 Delphi 2010 的机器上打开 `Win32VclShootingRange.dpr`。
2. 确认目标平台为 Win32，关闭 Runtime Packages（生成单文件 EXE）。
3. Build Project。
4. 生成的程序默认位于工程目录的 `Win32VclShootingRange.exe` 或 Delphi 配置的输出目录。

本机没有 Delphi 编译器，因此此工程未在当前环境实际编译；请同事编译后再进行 Inspect/UIA 验收。
