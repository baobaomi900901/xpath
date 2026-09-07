# xpath

## WEB GitHub Pages

首次启用：在仓库 Settings → Pages → Build and deployment → Source 中选择 GitHub Actions。
将改动推送到 main 后，Deploy WEB to GitHub Pages 工作流会自动构建 WEB 并发布 WEB/dist。
每次推送到 main 都会触发，不限制修改目录；也可在 Actions 中手动 Run workflow。

首次部署成功后的地址：https://baobaomi900901.github.io/xpath/
线上子页面使用 Hash 路由，例如 /xpath/#/form-controls，可直接打开和刷新。
本地 pnpm dev 保留原有路由。

GitHub Pages 仅托管静态页面，不能运行 SDK Cookie 观测所需的 /api/sdk-web/* 接口，
也不能提供本地 HTTP/HTTPS 测试域名及 Vite 插件的下载响应头。
Cookie 服务端测试请继续使用本地靶场；fetch + Blob 下载仍可在线使用。

本地验证 Pages 构建（PowerShell）：

```powershell
cd WEB
pnpm install --frozen-lockfile
$env:VITE_GITHUB_PAGES = 'true'
pnpm run build --base /xpath/
Remove-Item Env:VITE_GITHUB_PAGES
```
