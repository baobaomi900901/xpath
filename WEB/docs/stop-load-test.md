# stop_load 网络慢加载靶场

新增文件位于 `WEB/public/stop-load-test/`，可随现有 Vite 构建直接发布到 GitHub Pages，无外部延迟服务或后端依赖。

## 地址与操作

发布后先打开：

`https://baobaomi900901.github.io/xpath/stop-load-test/index.html`

等待 `#setup-state[data-state="ready"]`，点击“开始测试”。慢加载页为：

`https://baobaomi900901.github.io/xpath/stop-load-test/loading.html?delay=30000`

首次进入须先打开准备页注册 worker；直接打开慢加载页而没有 controller 时会明确显示“未准备”，不能将该次加载作为验收。首页菜单“停止网络加载测试”指向准备页。

默认资源等待 30000ms，可用 `delay` 指定 1000–120000ms 的整数。UI 输入单位为秒。`run` 标识本次加载，准备页每次生成随机值；SDK 脚本也应提供唯一 run，以便独立关联网络事件。

## 实现与判据

Service Worker 只注册在 `/xpath/stop-load-test/`；只延迟同目录 `slow.svg`，不缓存、不拦截其他靶场。

慢加载页在文档 `load` 之前插入图片。worker 使用异步定时等待，再读取同目录静态 SVG 并释放响应。该图片是浏览器待完成资源请求，等待时文档应为 `interactive`、load 事件计数为 0、页面 JS 心跳继续增长。该场景验证浏览器资源加载中止，延迟由 worker 提供，不是远端服务器响应耗时测试。

`window.stopLoadTest.getState()` 提供只读快照，包括：

- `controlled`：本目录 worker 是否控制当前页面。
- `delayMs`、`runId`：延迟与本次身份。
- `readyState`、`heartbeat`、`elapsedMs`：文档阶段、JS 活性及耗时。
- `resourceStatus`、`resourceLoaded`：pending / loaded / error / not-prepared，及图片是否完整返回。
- `loadEvents`、`events`：窗口 load 及资源/worker 事件记录。

停载后要同时检查：调用返回、文档结束加载、图片未完成、网络层 slow.svg 被取消；CDP 的 `Network.loadingFailed` 应有 `canceled=true` 和 `net::ERR_ABORTED`。页面 `resource_error` 单独不能区分停载与网络失败。自然完成对照应有 `resourceLoaded=true` 和一次窗口 load。页面不自动调用 window.stop 或停止加载 API。

## SDK 使用顺序

1. SDK 创建本次准备页，等待 ready 状态。
2. 在同一浏览器配置中导航到慢加载页；使用短于资源延迟的 load_timeout，预期等待超时。
3. 复核 controller、JS 心跳、interactive、资源 pending，确认仍在加载中。
4. 调用本次页面对象的 stop_load()，通过独立通道核对资源中止。
5. 返回准备页，点击“清理测试环境”，关闭本次标签。只注销本目录 registration；其他 worker 保留。

这是靶场的浏览器验证，不等于 UIAutoma SDK 已完成真实验收；SDK 正式测试在发布后进行。

## 本地浏览器回归

`WEB/tests/stop-load-test.mjs` 使用 Node、可导入的 Playwright 包和已安装的 Chrome。可通过 `STOP_LOAD_PLAYWRIGHT_MODULE` 指定现有 Playwright 包路径。测试自行启动临时 HTTP 服务，在独立无界面 Chrome 中验证 `/xpath/` 基路径，最后关闭浏览器和服务。

```powershell
cd WEB
node .\tests\stop-load-test.mjs
```

测试覆盖准备、主线程活性、停载前后及网络取消、自然完成对照、作用域隔离、注销。`pnpm run build --base /xpath/` 沿用项目现有 Pages 构建方式，构建后用 `node .\tests\stop-load-test.mjs --built` 对 `dist` 运行相同验证。

## 本轮验证记录

2026-10-05：源码靶场 6/6 PASS，GitHub Pages 构建成功，构建产物 6/6 PASS。构建产物通过默认“开始测试”按钮进入 30 秒等待页；停载后在 944ms 读到 complete、图片未完成，独立网络事件为 canceled=true / net::ERR_ABORTED。1.2 秒自然完成对照在 1233ms 读到图片完成和一次 load。正式 SDK 验收尚待发布后进行。
