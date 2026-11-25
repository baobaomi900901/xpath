# 元素串匹配测试实施计划

**Goal:** 增加可供外部自动化工具验证 14 种匹配规则的真实 DOM 靶场。

**Architecture:** 在现有 React 路由与首页添加独立页面。随机值存于页面状态，规则参考随样本状态更新，固定样本保持稳定。

**Tech Stack:** React 19、TypeScript、Ant Design 5、Vite 6、Playwright 浏览器验收。

## 约束

- 遵循已确认设计 `docs/superpowers/specs/2026-11-25-element-match-design.md`。
- 不增加依赖；不改动已有未提交工作；不发布或提交。
- 在当前会话内执行，先写浏览器验收并确认新增入口缺失，再实现和验证。

## 步骤

- [x] 新建 `WEB/tests/element-match-test.mjs`：从首页打开页面，读取真实按钮属性，独立验证全部规则的正反例和数值边界；验证随机位数、重新生成、刷新、点击反馈与移动端。
- [x] 运行浏览器验收，确认失败原因为首页没有新增入口。
- [x] 新建 `WEB/src/pages/ElementMatchTestPage.tsx`：真实原生按钮靶标、随机生成设置、点击反馈、14 行参考表。
- [x] 更新 `WEB/src/App.tsx` 路由、`WEB/src/pages/HomePage.tsx` 首页入口、`WEB/src/index.css` 页面布局、`README.md` 使用与验收说明。
- [x] 执行 `npm run build` 和浏览器验收，审查差异，记录实际结果。

## 验证结果

- `npm run build`：TypeScript 与 Vite 构建通过；Vite 提示主资源包超过 500 kB。
- `node tests/element-match-test.mjs`：4 组浏览器验收通过，包括 14 种规则、1/8/12/32 位随机码、非法输入、固定样本稳定性、点击反馈、刷新和 375px 窄屏；无页面异常。
- 已查看桌面与窄屏截图：`artifacts/element-match/element-match-desktop.png`、`artifacts/element-match/element-match-mobile.png`。
- `git diff --check`：通过。
