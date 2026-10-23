# Bank Transfer Range Implementation Plan

**Goal:** 将登录成功页面替换为可重建随机 DOM 的网银转账模拟表单。

**Architecture:** `utils/transferForm.ts` 定义字段、随机布局及校验；`pages/BankTransferPage.tsx` 管理输入、重建、确认与回执；`LoginTestPage.tsx` 只负责原有认证及登录后页面切换。随机布局仅在显式操作时生成，业务值与布局分开保存。

**Tech Stack:** React 19、TypeScript、Ant Design 5、原生表单控件、Vite、Playwright。

## Steps

- [x] 编写 `WEB/tests/bank-transfer-test.mjs`，先观察“登录后应显示网银转账表单”的断言失败。
- [x] 新建 `WEB/src/utils/transferForm.ts`，生成无业务含义的随机属性、七个字段顺序及 1–5 层包裹，显式重建保证顺序和深度变化；实现必填、账号及金额校验。
- [x] 新建 `WEB/src/pages/BankTransferPage.tsx`，实现网银表单、保留值重建、填写提示、确认摘要、模拟回执和继续转账。
- [x] 将 `LoginTestPage.tsx` 的成功视图替换为转账页，更新 `WEB/tests/login-test.mjs` 的成功断言及首页说明。
- [x] 更新 README 和原登录设计中的登录后行为。
- [x] 验证完整浏览器流程、窄屏截图、构建及 GitHub Pages 模式，复核代码与随机 DOM。

## Verification

- 首次浏览器验收按预期失败：登录后转账表单数量为 0。
- 本地登录回归：26 项检查通过；本地转账验收：10 项检查通过。
- GitHub Pages `/xpath/#/` 构建产物：10 项转账检查通过，包含两种登录及四轮连续随机重建。
- 普通构建、Pages 构建、测试脚本语法检查及 `git diff --check` 通过；保留现有打包体积提示。
- 已查看桌面和 375px 窄屏截图；只读代码复核未发现需要修复的问题。

## Follow-up: 内置 CS 鉴权流水号数据

- [x] 建立共用 `fixtures/bank-transfer-auth.json`，保存 10 条唯一、固定的流水号。
- [x] 扩展转账验收，观察旧随机流水号与固定清单第 1 条不一致的预期失败。
- [x] 二次确认后依次使用固定清单，10 条循环；表单校验、取消及重置不消耗流水号。
- [x] 增加共用数据说明并同步设计与 README，供后续 CS 端按流水号精确匹配。
- [x] 验证完整转账流程和 11 笔循环，执行构建检查。

验证结果：11 项浏览器检查通过，确认 10 个唯一固定流水号按清单顺序发放，第 11 笔回到第 1 条，确认取消及重置不消耗数据。`pnpm build`、`git diff --check` 与测试脚本语法检查通过。

## Follow-up: 二次确认提前显示流水号

- [x] 复现并增加断言：二次确认弹窗缺少业务流水号。
- [x] 打开确认弹窗时读取并保存当前待使用的流水号，与转账信息一起形成不可变快照；实际提交才推进序列，回执复用快照编号。
- [x] 验证取消重开不换号，全部 10 组及第 11 笔循环中弹窗与回执编号一致；11 项浏览器检查、类型检查和生产构建通过。

## Follow-up: 共享密钥随机流水号

后续需求已用 HMAC-SHA256 替换上述固定清单和序列逻辑。每次打开二次确认按金额、共享密钥与新随机因子生成编号，取消后重开会换号；确认与回执仍共用同一编号。实现与最终验收记录见 [共享密钥方案](2026-10-22-issued-reference.md)。
