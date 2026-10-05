# stop_load 静态靶场实现计划

目标：在 GitHub Pages 上提供持续加载、主线程可运行的页面，验证 Page.stopLoading 取消待完成资源请求。

方案：Service Worker 仅作用于 stop-load-test/，延迟 slow.svg 的响应；index.html 准备 worker，loading.html 在文档解析期间发起资源加载。所有链接均为相对路径，兼容 /xpath/ 发布基路径。

- [x] 浏览器回归先确认入口缺失时失败（HTTP 404，退出码 1）。
- [x] 新增准备页、慢加载页、作用域内 worker、样式与 SVG。
- [x] 首页增加入口；说明两阶段操作、状态读出与清理。
- [x] 独立验证：加载前 readyState=interactive、JS 心跳增长、资源 pending；CDP 停载后 slow.svg 出现 net::ERR_ABORTED；无停载对照自然完成。
- [x] 验证作用域隔离、注销和 /xpath/ 路径。
- [x] 运行 Pages 构建，保留浏览器验证输出。

2026-10-05：源码目录 6/6 PASS；Pages 构建成功；dist 目录 6/6 PASS。
构建产物实测：默认 30 秒资源在 944ms 时已被停载，网络事件 canceled=true；1.2 秒自然完成对照在 1233ms 完成。

不使用同步阻塞、外部延迟服务、缓存或全站 Service Worker。stop_load SDK 正式验收在用户发布后另行进行。
