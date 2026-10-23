# Iframe Registration Implementation Plan

**Goal:** 新增标题为“登记”的 iframe 表单，填写转账确认信息；按最新需求用共享密钥及金额校验随机业务流水号。

**Architecture:** `RegistrationPage.tsx` 导出外层 iframe 页面与内部登记表单；复用 `TRANSFER_FIELDS`、转账校验和共用 JSON。`transferReceipt.ts` 调用共用 HMAC 模块校验流水号及金额；新增两个路由及首页入口。

**Tech Stack:** React 19、TypeScript、Ant Design 5、Vite、原生 iframe、Playwright。

## Steps

- [x] 编写 `WEB/tests/registration-test.mjs`，先验证新增首页入口不存在时失败。
- [x] 最初完成固定清单校验，随后按最新需求替换为共享密钥、金额与随机因子的 HMAC 验签。
- [x] 实现外层 iframe 容器、内部 8 字段表单、重置/登记按钮和 iframe 内的校验/结果弹窗。
- [x] 注册两个路由，添加首页“登记”入口并更新 README。
- [x] 验证 10 条合法签名和非法数据、iframe 边界、Enter、重置、窄屏；运行生产构建与 Pages 模式检查，并复核代码。

## Verification

- 本地开发版和 Pages `/xpath/#/` 构建产物分别通过 10 项浏览器检查，包含从网银二次确认获取实际编号后登记，以及独立 Node HMAC 生成的编号验签。
- 拒绝旧固定编号、错误密钥、签名篡改、金额不匹配和非法表单值；模态弹窗均位于 iframe 内。
- 修复异步校验加载图标改变按钮可访问名称的问题，登记按钮使用稳定的名称。
- TypeScript 检查、生产构建、脚本语法检查及 `git diff --check` 通过；桌面和 375px 截图已查看，长流水号正常换行。
- 只读代码复核未发现需要修复的问题；保留项目原有打包体积提示。
