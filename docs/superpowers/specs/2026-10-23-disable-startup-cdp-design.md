# 禁止浏览器靶场通过启动配置开启 CDP

日期：2026-10-23。用户已授权实施和打包。

## 行为

CEF、Electron、WebView2 在添加 CDP 启动参数时仍正常打开窗口，但不创建 CDP 端口或 pipe 通道。直接启动 EXE 也生效。Python 启动器兼容并忽略旧调试参数，不再转发或宣传开启 CDP 的用法。

## 实现

- CEF：禁用标准 Chromium 命令行配置，保持调试端口为零；自定义 base-url 独立解析。
- Electron：主进程同步入口移除 remote-debugging-port、remote-debugging-pipe、remote-debugging-address，不从应用参数重新添加。base-url 正常工作。
- WebView2：创建环境前强制覆盖附加浏览器参数，阻断环境变量和注册表参数回退；清除调试器相关环境变量，并消除宿主 edge-webview-switches 的嵌套注入入口。配置仅影响当前进程及其子进程。
- 三者均不添加测试后门；旧 CDP 深度验收不再适用于发布产物，改为端口关闭及原生窗口冒烟验收。

## 验收与交付

- CEF 109、125、128、133、154；Electron 22、29、38、44；WebView2 Release 全部重新构建或打包。
- 测试普通启动、等号/分离形式的端口参数、重复参数、端口 0、pipe；WebView2 额外检查环境变量与嵌套参数。
- 验证进程存活、窗口可用、无 CDP 监听；测试只关闭自己启动的实例。
- 更新现行说明，明确已撤除的 CDP DOM 深度验收覆盖。
- 打包完整运行目录为可分发 ZIP，并附 SHA256 和本次验收结果。
