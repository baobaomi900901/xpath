# Excel 插件靶场 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 造一个可安装进 Excel 桌面版的 Office 加载项靶场:Ribbon 出现 "Excel 靶场插件",面板内完成 点击登录 → admin/1 登录 → 已登录 → admin ▾ → 退出登录 的完整交互。

**Architecture:** 纯静态 HTML/CSS/JS 加载项(零 npm 依赖),由 Python 标准库 HTTPS 服务托管在 `https://localhost:7300`;`manifest.xml` 通过复制到 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` 完成 sideload;证书用 PowerShell `New-SelfSignedCertificate` 生成并信任到 `Cert:\CurrentUser\Root`(免管理员)。

**Tech Stack:** Office.js 加载项 (AddInCommands 1.1 + VersionOverrides) / 原生 HTML+CSS+ES5 JS / Python 3 标准库 (`http.server`, `ssl`, `winreg`) / PowerShell (证书)。

**Spec:** `docs/superpowers/specs/2026-09-17-excel-addin-range-design.md`

## Global Constraints

- 插件名(选项卡 / 默认显示名):`Excel 靶场插件`;分组名:`登录靶场`;按钮名:`打开面板`。
- 固定端口 `7300`,固定地址 `https://localhost:7300`;服务只监听 `127.0.0.1`。
- 凭据硬编码:`admin` / `1`;失败文案固定为 `账号或密码错误`;不发起任何网络请求。
- 关键元素必须带 `data-testid`,取值与元素 `id` 完全一致(契约见 Task 2 表)。
- 不引入任何第三方依赖:不用 npm、不用 pip 包,只用 Python 标准库与 PowerShell。
- 登录态不持久化:不得使用 `localStorage` / `sessionStorage` / Cookie。
- 服务响应必须带 `Cache-Control: no-store`。
- git 提交信息前缀统一为 `office:`。

---

### Task 1: 插件骨架 — Ribbon manifest 与图标

**Files:**
- Create: `OFFICE/excel-addin/manifest.xml`
- Create: `OFFICE/excel-addin/assets/generate_icons.py`
- Create: `OFFICE/excel-addin/assets/icon-16.png`、`icon-32.png`、`icon-80.png`(由脚本生成)
- Create: `OFFICE/excel-addin/.gitignore`

**Interfaces:**
- Consumes: 无
- Produces: `manifest.xml` 中的三个 URL 资源 —— `https://localhost:7300/src/taskpane.html`(Task 2 创建)、`https://localhost:7300/src/commands.html`(Task 2 创建)、图标路径 `https://localhost:7300/assets/icon-{16,32,80}.png`;字符串替换锚点固定为字面量 `localhost:7300`(Task 5 的端口改写依赖它)。

- [ ] **Step 1: 写图标生成脚本**

Create `OFFICE/excel-addin/assets/generate_icons.py`:

```python
"""用 Python 标准库生成插件所需的 PNG 图标(无需 Pillow)。"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent
GREEN = (33, 115, 70)
WHITE = (255, 255, 255)


def _chunk(tag: bytes, data: bytes) -> bytes:
    payload = tag + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def _pixel(x: int, y: int, size: int) -> tuple[int, int, int]:
    margin = max(1, size // 8)
    border = margin * 2
    if x < border or y < border or x >= size - border or y >= size - border:
        return WHITE
    # 左上到右下的对角线 + 右上到左下的对角线, 组成 X
    if abs(x - y) <= margin or abs((size - 1 - x) - y) <= margin:
        return WHITE
    return GREEN


def render_png(size: int) -> bytes:
    rows = bytearray()
    for y in range(size):
        rows.append(0)  # filter type 0
        for x in range(size):
            rows.extend(_pixel(x, y, size))
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + _chunk(b"IEND", b"")
    )


def main() -> int:
    for size in (16, 32, 80):
        target = OUTPUT_DIR / f"icon-{size}.png"
        target.write_bytes(render_png(size))
        print(f"已生成 {target} ({target.stat().st_size} 字节)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 生成图标并验证是合法 PNG**

Run:
```powershell
python OFFICE\excel-addin\assets\generate_icons.py
python -c "import struct,pathlib; [print(p.name, struct.unpack('>II', p.read_bytes()[16:24])) for p in sorted(pathlib.Path('OFFICE/excel-addin/assets').glob('*.png'))]"
```
Expected: 三行输出,分别打印 `(16, 16)`、`(32, 32)`、`(80, 80)`。

- [ ] **Step 3: 写 manifest.xml**

Create `OFFICE/excel-addin/manifest.xml`(Id 用固定 GUID,不要改):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:bt="http://schemas.microsoft.com/office/officeappbasictypes/1.0"
           xmlns:ov="http://schemas.microsoft.com/office/taskpaneappversionoverrides"
           xsi:type="TaskPaneApp">
  <Id>7f3a9c21-4b8e-4d6a-9f10-2c5e8b7a4d31</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>xpath</ProviderName>
  <DefaultLocale>zh-CN</DefaultLocale>
  <DisplayName DefaultValue="Excel 靶场插件"/>
  <Description DefaultValue="Excel 靶场插件: 登录 / 退出登录 交互靶场。"/>
  <IconUrl DefaultValue="https://localhost:7300/assets/icon-32.png"/>
  <HighResolutionIconUrl DefaultValue="https://localhost:7300/assets/icon-80.png"/>
  <SupportUrl DefaultValue="https://localhost:7300/src/taskpane.html"/>
  <AppDomains>
    <AppDomain>https://localhost:7300</AppDomain>
  </AppDomains>
  <Hosts>
    <Host Name="Workbook"/>
  </Hosts>
  <Requirements>
    <Sets DefaultMinVersion="1.1">
      <Set Name="ExcelApi" MinVersion="1.1"/>
    </Sets>
  </Requirements>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:7300/src/taskpane.html"/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
  <VersionOverrides xmlns="http://schemas.microsoft.com/office/taskpaneappversionoverrides" xsi:type="VersionOverridesV1_0">
    <Hosts>
      <Host xsi:type="Workbook">
        <DesktopFormFactor>
          <FunctionFile resid="Commands.Url"/>
          <ExtensionPoint xsi:type="PrimaryCommandSurface">
            <CustomTab id="XPathRangeTab">
              <Group id="XPathRangeGroup">
                <Label resid="GroupLabel"/>
                <Icon>
                  <bt:Image size="16" resid="Icon16"/>
                  <bt:Image size="32" resid="Icon32"/>
                  <bt:Image size="80" resid="Icon80"/>
                </Icon>
                <Control xsi:type="Button" id="OpenTaskpaneButton">
                  <Label resid="ButtonLabel"/>
                  <Supertip>
                    <Title resid="ButtonLabel"/>
                    <Description resid="ButtonTip"/>
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon16"/>
                    <bt:Image size="32" resid="Icon32"/>
                    <bt:Image size="80" resid="Icon80"/>
                  </Icon>
                  <Action xsi:type="ShowTaskpane">
                    <TaskpaneId>XPathRangeTaskpane</TaskpaneId>
                    <SourceLocation resid="Taskpane.Url"/>
                  </Action>
                </Control>
              </Group>
              <Label resid="TabLabel"/>
            </CustomTab>
          </ExtensionPoint>
        </DesktopFormFactor>
      </Host>
    </Hosts>
    <Resources>
      <bt:Images>
        <bt:Image id="Icon16" DefaultValue="https://localhost:7300/assets/icon-16.png"/>
        <bt:Image id="Icon32" DefaultValue="https://localhost:7300/assets/icon-32.png"/>
        <bt:Image id="Icon80" DefaultValue="https://localhost:7300/assets/icon-80.png"/>
      </bt:Images>
      <bt:Urls>
        <bt:Url id="Taskpane.Url" DefaultValue="https://localhost:7300/src/taskpane.html"/>
        <bt:Url id="Commands.Url" DefaultValue="https://localhost:7300/src/commands.html"/>
      </bt:Urls>
      <bt:ShortStrings>
        <bt:String id="TabLabel" DefaultValue="Excel 靶场插件"/>
        <bt:String id="GroupLabel" DefaultValue="登录靶场"/>
        <bt:String id="ButtonLabel" DefaultValue="打开面板"/>
      </bt:ShortStrings>
      <bt:LongStrings>
        <bt:String id="ButtonTip" DefaultValue="打开 Excel 靶场插件面板"/>
      </bt:LongStrings>
    </Resources>
  </VersionOverrides>
</OfficeApp>
```

- [ ] **Step 4: 写 .gitignore**

Create `OFFICE/excel-addin/.gitignore`:

```
.certs/
```

- [ ] **Step 5: 验证 manifest 是合法 XML 且必需节点齐全**

Run:
```powershell
python -c "import xml.etree.ElementTree as ET; t=ET.parse(r'OFFICE/excel-addin/manifest.xml'); r=t.getroot(); ov=[e for e in r if e.tag.endswith('VersionOverrides')][0]; ns={'ov':'http://schemas.microsoft.com/office/taskpaneappversionoverrides'}; tab=ov.find('.//ov:CustomTab',ns); assert tab.get('id')=='XPathRangeTab'; labels=[e.text for e in ov.findall('.//ov:String',{'ov':'http://schemas.microsoft.com/office/officeappbasictypes/1.0'})]; print(labels); assert 'Excel 靶场插件' in labels and '登录靶场' in labels and '打开面板' in labels; print('manifest OK')"
```
Expected: 打印字符串列表(含 `Excel 靶场插件` / `登录靶场` / `打开面板`)后输出 `manifest OK`;任何 AssertionError 都说明节点写错。

- [ ] **Step 6: Commit**

```bash
git add OFFICE/excel-addin/manifest.xml OFFICE/excel-addin/.gitignore OFFICE/excel-addin/assets
git commit -m "office: 新增 Excel 插件靶场 manifest 与图标"
```

---

### Task 2: 任务窗格 — 登录 / 已登录 / 用户菜单 交互

**Files:**
- Create: `OFFICE/excel-addin/src/taskpane.html`
- Create: `OFFICE/excel-addin/src/taskpane.css`
- Create: `OFFICE/excel-addin/src/taskpane.js`
- Create: `OFFICE/excel-addin/src/commands.html`
- Create: `OFFICE/excel-addin/src/commands.js`

**Interfaces:**
- Consumes: Task 1 的 manifest 中引用的 `src/taskpane.html` 与 `src/commands.html` 两个路径。
- Produces: 元素契约(Task 4 / Task 5 的验证脚本按此定位)——

| id = data-testid | 元素 | 文案 | 可见状态 |
|---|---|---|---|
| `login-trigger` | `button` | `点击登录` | 未登录 |
| `login-dialog` | `div` 遮罩容器 | — | 弹窗打开 |
| `username-input` | `input[type=text]` | — | 弹窗打开 |
| `password-input` | `input[type=password]` | — | 弹窗打开 |
| `login-submit` | `button[type=submit]` | `登录` | 弹窗打开 |
| `login-cancel` | `button` | `取消` | 弹窗打开 |
| `login-error` | `p[role=alert]` | `账号或密码错误` | 校验失败 |
| `login-status` | `span` | `已登录` | 已登录 |
| `user-menu-trigger` | `button`(内含 `▾`) | `admin` | 已登录 |
| `user-menu` | `div[role=menu]` | — | 菜单展开 |
| `logout-item` | `button` | `退出登录` | 菜单展开 |
| `user-menu-name` | `span` | `admin` | 已登录 |

  另外 `window.__xpathRange.getState()` 返回 `{loggedIn, dialogOpen, menuOpen, error}` 快照,供验证脚本断言内部状态。

- [ ] **Step 1: 写 commands.html / commands.js(Office 运行时占位)**

Create `OFFICE/excel-addin/src/commands.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>Excel 靶场插件 - 命令页</title>
    <script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"></script>
    <script src="commands.js"></script>
  </head>
  <body></body>
</html>
```

Create `OFFICE/excel-addin/src/commands.js`:

```js
(function () {
  'use strict';
  // 本靶场没有 Ribbon 函数命令, 此文件仅满足 Office 运行时对 FunctionFile 的要求。
  if (typeof Office !== 'undefined' && Office.onReady) {
    Office.onReady(function () {});
  }
})();
```

- [ ] **Step 2: 写 taskpane.html(元素契约的载体)**

Create `OFFICE/excel-addin/src/taskpane.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Excel 靶场插件</title>
    <link rel="stylesheet" href="taskpane.css" />
    <script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"></script>
  </head>
  <body>
    <header class="pane-header">
      <span class="pane-title">Excel 靶场插件</span>
      <span id="login-status" data-testid="login-status" class="pane-status" hidden>已登录</span>
    </header>

    <main class="pane-body">
      <div class="account-slot">
        <button id="login-trigger" data-testid="login-trigger" type="button" class="btn btn-primary">点击登录</button>

        <button id="user-menu-trigger" data-testid="user-menu-trigger" type="button" class="btn btn-user"
                aria-haspopup="menu" aria-expanded="false" aria-controls="user-menu" hidden>
          <span id="user-menu-name" data-testid="user-menu-name">admin</span>
          <span class="caret" aria-hidden="true">&#9662;</span>
        </button>

        <div id="user-menu" data-testid="user-menu" class="user-menu" role="menu" hidden>
          <button id="logout-item" data-testid="logout-item" type="button" class="user-menu-item" role="menuitem">退出登录</button>
        </div>
      </div>
    </main>

    <div id="login-dialog" data-testid="login-dialog" class="dialog-backdrop" hidden>
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="login-dialog-title">
        <h2 id="login-dialog-title" class="dialog-title">登录</h2>
        <form id="login-form" novalidate>
          <label class="field" for="username-input">名称</label>
          <input id="username-input" data-testid="username-input" name="username" type="text" autocomplete="off" />
          <label class="field" for="password-input">密码</label>
          <input id="password-input" data-testid="password-input" name="password" type="password" autocomplete="off" />
          <p id="login-error" data-testid="login-error" class="dialog-error" role="alert" hidden>账号或密码错误</p>
          <div class="dialog-actions">
            <button id="login-cancel" data-testid="login-cancel" type="button" class="btn">取消</button>
            <button id="login-submit" data-testid="login-submit" type="submit" class="btn btn-primary">登录</button>
          </div>
        </form>
      </div>
    </div>

    <script src="taskpane.js"></script>
  </body>
</html>
```

- [ ] **Step 3: 写 taskpane.css**

Create `OFFICE/excel-addin/src/taskpane.css`:

```css
:root { color-scheme: light; }

* { box-sizing: border-box; }

[hidden] { display: none !important; }

body {
  margin: 0;
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
  font-size: 14px;
  color: #201f1e;
  background: #ffffff;
}

.pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #edebe9;
}

.pane-title { font-weight: 600; }

.pane-status { color: #107c10; font-weight: 600; }

.pane-body { padding: 16px; }

.account-slot { position: relative; display: inline-block; }

.btn {
  font: inherit;
  cursor: pointer;
  padding: 6px 14px;
  border: 1px solid #8a8886;
  border-radius: 4px;
  background: #ffffff;
  color: #201f1e;
}

.btn:hover { background: #f3f2f1; }

.btn-primary { background: #217346; border-color: #217346; color: #ffffff; }

.btn-primary:hover { background: #1b5e39; }

.btn-user { display: inline-flex; align-items: center; gap: 6px; }

.caret { font-size: 10px; line-height: 1; }

.user-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 20;
  min-width: 140px;
  padding: 4px;
  border: 1px solid #edebe9;
  border-radius: 4px;
  background: #ffffff;
  box-shadow: 0 3.2px 7.2px rgba(0, 0, 0, 0.13);
}

.user-menu-item {
  display: block;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 2px;
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.user-menu-item:hover { background: #f3f2f1; }

.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
}

.dialog {
  width: min(320px, calc(100% - 32px));
  padding: 16px;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.dialog-title { margin: 0 0 12px; font-size: 16px; }

.field { display: block; margin: 8px 0 4px; font-size: 12px; color: #605e5c; }

.dialog input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #8a8886;
  border-radius: 4px;
  font: inherit;
}

.dialog input:focus { outline: 2px solid #217346; outline-offset: -1px; border-color: #217346; }

.dialog-error { margin: 10px 0 0; color: #a4262c; font-size: 12px; }

.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
```

- [ ] **Step 4: 写 taskpane.js(状态机)**

Create `OFFICE/excel-addin/src/taskpane.js`:

```js
(function () {
  'use strict';

  var EXPECTED_USERNAME = 'admin';
  var EXPECTED_PASSWORD = '1';

  var state = { loggedIn: false, dialogOpen: false, menuOpen: false, error: false };
  var refs = {};

  [
    'login-trigger', 'login-dialog', 'login-form', 'username-input', 'password-input',
    'login-submit', 'login-cancel', 'login-error', 'login-status',
    'user-menu', 'user-menu-trigger', 'user-menu-name', 'logout-item'
  ].forEach(function (id) {
    refs[id] = document.getElementById(id);
  });

  function render() {
    refs['login-dialog'].hidden = !state.dialogOpen;
    refs['login-trigger'].hidden = state.loggedIn;
    refs['login-status'].hidden = !state.loggedIn;
    refs['user-menu-trigger'].hidden = !state.loggedIn;
    refs['user-menu'].hidden = !(state.loggedIn && state.menuOpen);
    refs['user-menu-trigger'].setAttribute('aria-expanded', state.loggedIn && state.menuOpen ? 'true' : 'false');
    refs['login-error'].hidden = !state.error;
  }

  function openDialog() {
    state.dialogOpen = true;
    state.error = false;
    refs['username-input'].value = '';
    refs['password-input'].value = '';
    render();
    refs['username-input'].focus();
  }

  function closeDialog() {
    state.dialogOpen = false;
    state.error = false;
    render();
  }

  function submitLogin() {
    var name = refs['username-input'].value.trim();
    var password = refs['password-input'].value;
    if (name !== EXPECTED_USERNAME || password !== EXPECTED_PASSWORD) {
      state.error = true;
      render();
      return;
    }
    state.loggedIn = true;
    state.dialogOpen = false;
    state.menuOpen = false;
    state.error = false;
    refs['user-menu-name'].textContent = EXPECTED_USERNAME;
    render();
  }

  function toggleMenu() {
    if (!state.loggedIn) return;
    state.menuOpen = !state.menuOpen;
    render();
  }

  function logout() {
    state.loggedIn = false;
    state.dialogOpen = false;
    state.menuOpen = false;
    state.error = false;
    render();
  }

  refs['login-trigger'].addEventListener('click', openDialog);
  refs['login-cancel'].addEventListener('click', closeDialog);
  // 点击时阻止原生提交, 避免 click 与 submit 双触发; 回车仍走 form 的 submit。
  refs['login-submit'].addEventListener('click', function (event) {
    event.preventDefault();
    submitLogin();
  });
  refs['login-form'].addEventListener('submit', function (event) {
    event.preventDefault();
    submitLogin();
  });
  refs['user-menu-trigger'].addEventListener('click', function (event) {
    event.stopPropagation();
    toggleMenu();
  });
  refs['logout-item'].addEventListener('click', function (event) {
    event.stopPropagation();
    logout();
  });
  document.addEventListener('click', function () {
    if (state.menuOpen) {
      state.menuOpen = false;
      render();
    }
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && state.dialogOpen) closeDialog();
  });

  window.__xpathRange = {
    getState: function () {
      return {
        loggedIn: state.loggedIn,
        dialogOpen: state.dialogOpen,
        menuOpen: state.menuOpen,
        error: state.error
      };
    }
  };

  render();

  // 在浏览器里直接打开(无 Office 宿主)时静默降级, 不影响靶场交互。
  if (typeof Office !== 'undefined' && Office.onReady) {
    Office.onReady(function () {});
  }
})();
```

- [ ] **Step 5: 验证元素契约完整(静态检查)**

Run:
```powershell
python -c "import re,pathlib; html=pathlib.Path('OFFICE/excel-addin/src/taskpane.html').read_text(encoding='utf-8'); ids=['login-trigger','login-dialog','login-form','username-input','password-input','login-submit','login-cancel','login-error','login-status','user-menu','user-menu-trigger','user-menu-name','logout-item']; missing=[i for i in ids if ('id=\"%s\"'%i) not in html or ('data-testid=\"%s\"'%i) not in html]; print('missing:',missing); assert not missing; print('contract OK')"
```
Expected: `missing: []` 然后 `contract OK`。

- [ ] **Step 6: Commit**

```bash
git add OFFICE/excel-addin/src
git commit -m "office: 新增 Excel 插件任务窗格登录交互"
```

---

### Task 3: 本地 HTTPS 服务与 localhost 证书

**Files:**
- Create: `tools/start_excel_addin.py`

**Interfaces:**
- Consumes: `OFFICE/excel-addin/manifest.xml`(Task 1)与整个 `OFFICE/excel-addin/` 目录作为静态根。
- Produces: 可执行 CLI `python tools/start_excel_addin.py [--port 7300] [--no-launch] [--renew-cert] [--skip-sideload]`;命令行行为:启动前先确保证书、sideload 并(默认)拉起 Excel,随后**前台阻塞**托管 HTTPS。Task 4 / Task 5 依赖 `https://localhost:7300/` 可用与 `--no-launch` 的存在。模块级常量 `SIDELOAD_NAME = "xpath-excel-addin.manifest.xml"`、`WEF_DIR`、`DEFAULT_PORT = 7300`、`PFX_PASSWORD` 供 Task 5 的卸载脚本按同名引用。

- [ ] **Step 1: 写证书 + 服务脚本**

Create `tools/start_excel_addin.py`:

```python
"""启动 Excel 插件靶场: localhost 证书 -> HTTPS 静态服务 -> sideload 到 Excel。"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import ssl
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDIN_DIR = REPO_ROOT / "OFFICE" / "excel-addin"
CERT_DIR = ADDIN_DIR / ".certs"
PFX_PATH = CERT_DIR / "localhost.pfx"
CER_PATH = CERT_DIR / "localhost.cer"
PFX_PASSWORD = "xpath-excel-addin"
DEFAULT_PORT = 7300
MANIFEST_PORT_ANCHOR = "localhost:7300"
SIDELOAD_NAME = "xpath-excel-addin.manifest.xml"
WEF_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Office" / "16.0" / "Wef"
EXCEL_REGISTRY_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe"


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def run_powershell(script: str) -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"PowerShell 执行失败: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def _escape(path: Path) -> str:
    return str(path).replace("'", "''")


def certificate_ready() -> bool:
    if not (PFX_PATH.exists() and CER_PATH.exists()):
        return False
    script = (
        "$cert = Get-ChildItem Cert:\\CurrentUser\\My | Where-Object { $_.Subject -eq 'CN=localhost' } "
        "| Sort-Object NotAfter -Descending | Select-Object -First 1; "
        "if ($cert -and $cert.NotAfter -gt (Get-Date).AddDays(30)) { 'ok' }"
    )
    try:
        return run_powershell(script).strip() == "ok"
    except RuntimeError:
        return False


def ensure_certificate(renew: bool) -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    if not renew and certificate_ready():
        print(f"复用现有 localhost 证书: {PFX_PATH}")
        return

    print("正在创建并信任 localhost 证书 ...")
    script = f"""
$ErrorActionPreference = 'Stop'
Get-ChildItem Cert:\\CurrentUser\\My | Where-Object {{ $_.Subject -eq 'CN=localhost' }} | Remove-Item -Force
$cert = New-SelfSignedCertificate -DnsName 'localhost', '127.0.0.1' -Subject 'CN=localhost' `
    -CertStoreLocation Cert:\\CurrentUser\\My -NotAfter (Get-Date).AddYears(5) -FriendlyName 'xpath-excel-addin'
Export-PfxCertificate -Cert $cert -FilePath '{_escape(PFX_PATH)}' `
    -Password (ConvertTo-SecureString -String '{PFX_PASSWORD}' -Force -AsPlainText) | Out-Null
Export-Certificate -Cert $cert -FilePath '{_escape(CER_PATH)}' | Out-Null
Import-Certificate -FilePath '{_escape(CER_PATH)}' -CertStoreLocation Cert:\\CurrentUser\\Root | Out-Null
$cert.Thumbprint
"""
    thumbprint = run_powershell(script)
    print(f"证书已就绪: {thumbprint}")


class NoStoreHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - 与基类签名保持一致
        sys.stdout.write(f"[https] {self.address_string()} {format % args}\n")
        sys.stdout.flush()


def create_server(port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(NoStoreHandler, directory=str(ADDIN_DIR))
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as error:
        raise RuntimeError(f"端口 {port} 无法监听({error});请用 --port 指定其它端口。") from error
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_pkcs12(PFX_PATH.read_bytes(), PFX_PASSWORD)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    return httpd


def render_manifest(port: int) -> str:
    source = (ADDIN_DIR / "manifest.xml").read_text(encoding="utf-8")
    return source.replace(MANIFEST_PORT_ANCHOR, f"localhost:{port}")


def sideload(port: int) -> Path:
    WEF_DIR.mkdir(parents=True, exist_ok=True)
    target = WEF_DIR / SIDELOAD_NAME
    target.write_text(render_manifest(port), encoding="utf-8")
    return target


def find_excel() -> Path | None:
    try:
        import winreg
    except ImportError:
        return None
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, EXCEL_REGISTRY_KEY) as handle:
                return Path(winreg.QueryValue(handle, None))
        except OSError:
            continue
    return None


def excel_running() -> bool:
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE", "/NH"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return "EXCEL.EXE" in completed.stdout.upper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 Excel 插件靶场。")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"HTTPS 端口, 默认 {DEFAULT_PORT}。")
    parser.add_argument("--no-launch", action="store_true", help="不自动拉起 Excel。")
    parser.add_argument("--renew-cert", action="store_true", help="强制重建 localhost 证书。")
    parser.add_argument("--skip-sideload", action="store_true", help="只起服务, 不写入 Wef 目录。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    if not (ADDIN_DIR / "manifest.xml").is_file():
        print(f"错误: 找不到 {ADDIN_DIR / 'manifest.xml'}", file=sys.stderr)
        return 1

    ensure_certificate(args.renew_cert)

    if args.skip_sideload:
        print("已跳过 sideload。")
    else:
        try:
            target = sideload(args.port)
            print(f"已写入 sideload manifest: {target}")
        except OSError as error:
            print(f"错误: 写入 Wef 目录失败({error})。可用 --skip-sideload 只起服务。", file=sys.stderr)

    excel = find_excel()
    if excel is None:
        print("未检测到 Excel, 仅启动服务;请在装有 Excel 桌面版的机器上重复本步骤。")
    elif args.no_launch:
        print("已跳过启动 Excel。")
    elif excel_running():
        print("检测到 Excel 正在运行: 请完全退出并重新打开 Excel, Ribbon 才会出现新选项卡。")
    else:
        subprocess.Popen([str(excel)])
        print(f"已启动 Excel: {excel}")

    url = f"https://localhost:{args.port}/src/taskpane.html"
    print(f"\n服务地址: {url}")
    print("在 Excel 中: 顶部 'Excel 靶场插件' 选项卡 -> '打开面板'。")
    print("按 Ctrl+C 停止服务。\n")

    try:
        server = create_server(args.port)
    except RuntimeError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务。")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:  # noqa: BLE001 - CLI 顶层兜底
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
```

- [ ] **Step 2: 验证语法与帮助输出**

Run:
```powershell
python -m py_compile tools\start_excel_addin.py
python tools\start_excel_addin.py --help
```
Expected: 编译无输出(退出码 0);`--help` 列出 `--port`、`--no-launch`、`--renew-cert`、`--skip-sideload`。

- [ ] **Step 3: 生成证书并确认信任链**

Run:
```powershell
python tools\start_excel_addin.py --no-launch --skip-sideload --port 7300
```
Expected: 打印 `正在创建并信任 localhost 证书 ...`、`证书已就绪: <THUMBPRINT>`、服务地址 `https://localhost:7300/src/taskpane.html`,随后阻塞。
(若此步出现 `[sandbox: file access denied]`,说明证书库写入被沙箱拦截:用同一条命令申请一次工作区外写权限后重试;仍失败则把输出的 PowerShell 片段交给用户手动执行。)

- [ ] **Step 4: 服务探活(在另一个终端 / 后台作业中执行)**

先让 Step 3 的进程在后台运行,然后:
```powershell
curl.exe -k -s -o NUL -w "%{http_code}\n" https://localhost:7300/src/taskpane.html
curl.exe -s -o NUL -w "%{http_code}\n" https://localhost:7300/src/taskpane.html
```
Expected: 第一条 `200`;第二条也是 `200`(证书已受信任,无需 `-k`)。若第二条非 200,说明证书未进 `CurrentUser\Root`,回到 Step 3 加 `--renew-cert`。

- [ ] **Step 5: 验证 no-store 与静态资源**

Run:
```powershell
curl.exe -s -D - -o NUL https://localhost:7300/src/taskpane.html | Select-String -Pattern "HTTP/|Cache-Control"
curl.exe -s -o NUL -w "icon=%{http_code}\n" https://localhost:7300/assets/icon-32.png
```
Expected: 输出含 `HTTP/1.0 200`(或 1.1)与 `Cache-Control: no-store, no-cache, must-revalidate`;`icon=200`。

- [ ] **Step 6: Commit**

```bash
git add tools/start_excel_addin.py
git commit -m "office: 新增 Excel 插件靶场本地 HTTPS 启动器"
```

---

### Task 4: 浏览器端全流程验证(登录 → 已登录 → 退出登录)

**Files:**
- Create: `OFFICE/excel-addin/verify/verify-flow.mjs`
- Modify: 无(仅在流程发现问题时回改 Task 2 的 `src/taskpane.js` / `src/taskpane.html`)

**Interfaces:**
- Consumes: Task 2 的元素契约与 `window.__xpathRange.getState()`;Task 3 的 `https://localhost:7300/src/taskpane.html`。
- Produces: 可重复执行的验收命令 `node OFFICE/excel-addin/verify/verify-flow.mjs`,退出码 0 表示全部断言通过;不产出被其它任务消费的接口。

- [ ] **Step 1: 确认可用的浏览器自动化能力**

Run(加载 `agent-browser` 技能后按其说明执行):
```
agent-browser --help
```
Expected: 能看到打开页面、点击、填表、截图相关的子命令。若该 CLI 不可用,改用 `browser-use` 技能走同一条断言清单。

- [ ] **Step 2: 用真实浏览器走完整流程**

用 agent-browser 依次执行并记录每步结果(忽略自签证书错误):

1. 打开 `https://localhost:7300/src/taskpane.html`
2. 断言: `#login-trigger` 可见且文本为 `点击登录`;`#login-dialog` 不可见;`#user-menu-trigger` 不可见
3. 点击 `#login-trigger`
4. 断言: `#login-dialog` 可见,`#username-input`、`#password-input`(type=password)、`#login-submit` 均可见
5. 在 `#username-input` 输入 `admin`,在 `#password-input` 输入 `1`,点击 `#login-submit`
6. 断言: `#login-dialog` 不可见;`#login-status` 可见且文本为 `已登录`;`#login-trigger` 不可见;
   `#user-menu-trigger` 可见且文本包含 `admin` 与 `▾`;`window.__xpathRange.getState().loggedIn === true`
7. 点击 `#user-menu-trigger`
8. 断言: `#user-menu` 可见,`#logout-item` 可见且文本为 `退出登录`;`aria-expanded="true"`
9. 点击 `#logout-item`
10. 断言: `#login-trigger` 可见、`#user-menu-trigger` 不可见、`#login-status` 不可见;
    `getState()` 全部为 `false`
11. 截图保存为 `OFFICE/excel-addin/verify/screenshot-logged-in.png`(第 8 步后)与 `verify/screenshot-logged-out.png`(第 10 步后)

Expected: 10 步断言全部通过。

- [ ] **Step 3: 补测失败分支与取消分支**

1. 点击 `#login-trigger` → 输入 `admin` / `2` → 点击 `#login-submit`
2. 断言: `#login-dialog` 仍可见;`#login-error` 可见且文本为 `账号或密码错误`;`getState().loggedIn === false`
3. 点击 `#login-cancel`
4. 断言: `#login-dialog` 不可见,`#login-trigger` 可见

Expected: 全部通过。

- [ ] **Step 4: 把流程固化成可重复脚本**

Create `OFFICE/excel-addin/verify/verify-flow.mjs`(用 Node 内置 `fetch` 做静态契约兜底;真实点击断言由 Step 2/3 的浏览器会话人工复核,截图作为证据):

```js
// 用途: 在没有 Excel 的环境里做一次可重复的静态契约校验。
// 真实交互断言见同目录 README 描述的浏览器步骤与截图。
const BASE = process.env.XPATH_ADDIN_BASE ?? 'https://localhost:7300';
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const REQUIRED_IDS = [
  'login-trigger', 'login-dialog', 'login-form', 'username-input', 'password-input',
  'login-submit', 'login-cancel', 'login-error', 'login-status',
  'user-menu', 'user-menu-trigger', 'user-menu-name', 'logout-item'
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
  console.log(`  ok - ${message}`);
}

const response = await fetch(`${BASE}/src/taskpane.html`);
assert(response.status === 200, `taskpane.html 返回 200 (实际 ${response.status})`);
assert(
  (response.headers.get('cache-control') ?? '').includes('no-store'),
  'taskpane.html 带 Cache-Control: no-store'
);

const html = await response.text();
for (const id of REQUIRED_IDS) {
  assert(html.includes(`id="${id}"`) && html.includes(`data-testid="${id}"`), `元素契约存在: ${id}`);
}
assert(html.includes('点击登录'), '文案存在: 点击登录');
assert(html.includes('退出登录'), '文案存在: 退出登录');
assert(html.includes('已登录'), '文案存在: 已登录');
assert(html.includes('账号或密码错误'), '文案存在: 账号或密码错误');

const script = await (await fetch(`${BASE}/src/taskpane.js`)).text();
assert(script.includes("EXPECTED_USERNAME = 'admin'"), '凭据用户名为 admin');
assert(script.includes("EXPECTED_PASSWORD = '1'"), '凭据密码为 1');
assert(!script.includes('localStorage'), '未使用 localStorage');
assert(!script.includes('sessionStorage'), '未使用 sessionStorage');

const manifest = await (await fetch(`${BASE}/manifest.xml`)).text();
for (const text of ['Excel 靶场插件', '登录靶场', '打开面板']) {
  assert(manifest.includes(text), `manifest 文案: ${text}`);
}
assert(manifest.includes('XPathRangeTab'), 'manifest 自定义选项卡 id');

console.log('\n静态契约校验全部通过。');
```

- [ ] **Step 5: 运行固化脚本**

Run(需要 Task 3 的服务在运行):
```powershell
node OFFICE\excel-addin\verify\verify-flow.mjs
```
Expected: 逐条 `ok - ...`,最后输出 `静态契约校验全部通过。`,退出码 0。

- [ ] **Step 6: Commit**

```bash
git add OFFICE/excel-addin/verify
git commit -m "office: 新增 Excel 插件靶场契约校验脚本与截图"
```

---

### Task 5: 安装/卸载到 Excel(sideload)与 Excel 侧验证

**Files:**
- Create: `tools/stop_excel_addin.py`
- Test: 无自动化测试文件;验证靠命令行断言与 UIA 枚举

**Interfaces:**
- Consumes: Task 3 的 `WEF_DIR`、`SIDELOAD_NAME`、`PFX_PASSWORD`、`CERT_DIR`、`CER_PATH` 同名常量与 `run_powershell` 行为。
- Produces: `python tools/stop_excel_addin.py [--keep-cert] [--no-sideload]`,退出码 0 表示已清理;供用户与人工验证使用。

- [ ] **Step 1: 写卸载脚本**

Create `tools/stop_excel_addin.py`:

```python
"""卸载 Excel 插件靶场: 移除 sideload manifest, 可选移除 localhost 证书。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from start_excel_addin import (  # noqa: E402 - 复用启动器的常量与 PowerShell 桥
    CERT_DIR,
    CER_PATH,
    PFX_PATH,
    SIDELOAD_NAME,
    WEF_DIR,
    configure_output,
    run_powershell,
)


def remove_sideload() -> None:
    target = WEF_DIR / SIDELOAD_NAME
    if not target.exists():
        print(f"sideload manifest 不存在, 无需移除: {target}")
        return
    try:
        target.unlink()
    except OSError as error:
        raise RuntimeError(
            f"删除失败({error})。请完全退出 Excel 后重试, 或手动删除: {target}"
        ) from error
    print(f"已移除 sideload manifest: {target}")


def remove_certificate() -> None:
    script = """
$ErrorActionPreference = 'Continue'
Get-ChildItem Cert:\\CurrentUser\\Root | Where-Object { $_.Subject -eq 'CN=localhost' } | Remove-Item -Force
Get-ChildItem Cert:\\CurrentUser\\My | Where-Object { $_.Subject -eq 'CN=localhost' } | Remove-Item -Force
'removed'
"""
    print(run_powershell(script))
    for path in (PFX_PATH, CER_PATH):
        path.unlink(missing_ok=True)
    if CERT_DIR.exists() and not any(CERT_DIR.iterdir()):
        CERT_DIR.rmdir()
    print("已移除 localhost 证书。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="卸载 Excel 插件靶场。")
    parser.add_argument("--keep-cert", action="store_true", help="保留 localhost 证书。")
    parser.add_argument("--no-sideload", action="store_true", help="只处理证书, 不删除 sideload manifest。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    if args.no_sideload:
        print("已跳过 sideload 清理。")
    else:
        remove_sideload()

    if args.keep_cert:
        print("已保留 localhost 证书。")
    else:
        remove_certificate()

    print("\n请完全退出并重新打开 Excel, 'Excel 靶场插件' 选项卡才会消失。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:  # noqa: BLE001 - CLI 顶层兜底
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
```

- [ ] **Step 2: 验证安装动作真的写了 Wef manifest**

Run(先停掉 Task 3 的前台服务,再单独执行一次安装步骤):
```powershell
python -m py_compile tools\stop_excel_addin.py
python tools\start_excel_addin.py --no-launch --port 7300
```
在服务阻塞期间另开一个终端执行:
```powershell
python -c "import os,pathlib; p=pathlib.Path(os.environ['LOCALAPPDATA'])/'Microsoft/Office/16.0/Wef/xpath-excel-addin.manifest.xml'; print(p, p.exists(), p.stat().st_size if p.exists() else 0)"
```
Expected: 输出完整路径 + `True` + 大于 0 的字节数。
(若出现 `[sandbox: file access denied]`:这是工作区外写入,申请一次权限后重试;被拒则把 `start_excel_addin.py` 打印的目标路径交给用户手动复制。)

- [ ] **Step 3: 验证 Excel 菜单出现插件名**

Run(需要 Excel 已完全重启,且服务在运行):
```powershell
python -c "import subprocess,time; print('启动 Excel'); p=subprocess.Popen([r'C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE']); time.sleep(25); print('Excel 已启动, PID', p.pid)"
```
再用 UI Automation 枚举 Ribbon:
```powershell
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, 'Excel 靶场插件')
$el = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
if ($el) { "FOUND: " + $el.Current.ControlType.ProgrammaticName } else { "NOT FOUND" }
```
Expected: `FOUND: ControlType.TabItem`。若为 `NOT FOUND`:确认服务在跑、manifest 已写入 Wef、Excel 已重启;仍失败则检查
`%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` 下文件名后缀(必须是 `.xml`)。

- [ ] **Step 4: 验证卸载清理干净**

Run:
```powershell
python tools\stop_excel_addin.py --keep-cert
python -c "import os,pathlib; p=pathlib.Path(os.environ['LOCALAPPDATA'])/'Microsoft/Office/16.0/Wef/xpath-excel-addin.manifest.xml'; print('manifest exists:', p.exists())"
```
Expected: 打印 `已移除 sideload manifest: ...` 与 `manifest exists: False`。

- [ ] **Step 5: Commit**

```bash
git add tools/stop_excel_addin.py
git commit -m "office: 新增 Excel 插件靶场卸载脚本"
```

---

### Task 6: 使用说明与收尾

**Files:**
- Create: `OFFICE/excel-addin/README.md`
- Modify: `README.md`(仓库根,新增一节指向 Excel 插件靶场)

**Interfaces:**
- Consumes: Task 3 / Task 5 的 CLI 形态、Task 2 的元素契约表、Task 4 的校验命令。
- Produces: 面向使用者的文档;无代码接口。

- [ ] **Step 1: 写插件说明**

Create `OFFICE/excel-addin/README.md`,必须覆盖:

1. 一句话定位与"凭据 admin/1 仅靶场演示、无任何外发请求"的声明
2. 环境要求:Windows + Excel 桌面版(支持 AddInCommands 1.1)、Python 3.8+
3. 安装:`python tools/start_excel_addin.py` → 完全退出并重开 Excel → `Excel 靶场插件` 选项卡 → `打开面板`
4. 使用流程(6 步,含 `admin`/`1` 与 `退出登录`)
5. 卸载:`python tools/stop_excel_addin.py`(说明 `--keep-cert`)
6. 元素契约表(照抄 Task 2 的表格,注明自动化定位以 `data-testid` 为准)
7. 故障排查表:证书未信任 / 端口占用 / Excel 未出现选项卡 / 面板空白(右键重新加载)/ 沙箱拒绝写 Wef 目录时的手动复制命令
8. 无 Excel 时的验证方式:`python tools/start_excel_addin.py --no-launch --skip-sideload` + `node OFFICE/excel-addin/verify/verify-flow.mjs`

- [ ] **Step 2: 在仓库根 README 增加入口**

在 `README.md` 末尾追加一节:

```markdown
## Excel 插件靶场

在 Excel 桌面版安装一个 Office 加载项, 用于验证 Ribbon + WebView2 任务窗格场景
(点击登录 → admin/1 → 已登录 → 退出登录)。

```powershell
python tools/start_excel_addin.py
python tools/stop_excel_addin.py
```

详见 [OFFICE/excel-addin/README.md](OFFICE/excel-addin/README.md)。
```

- [ ] **Step 3: 端到端复跑一遍**

Run:
```powershell
python tools\start_excel_addin.py --no-launch --skip-sideload
```
在另一个终端:
```powershell
node OFFICE\excel-addin\verify\verify-flow.mjs
```
Expected: `静态契约校验全部通过。`

- [ ] **Step 4: Commit**

```bash
git add OFFICE/excel-addin/README.md README.md
git commit -m "office: 补充 Excel 插件靶场使用说明"
```

---

## 自检记录(写计划时执行)

- **Spec 覆盖**:§3 组件 → Task 1/2/3/5;§4.1 托管 → Task 3;§4.2 证书 → Task 3 Step 3-5;§4.3 sideload → Task 3 Step 1 + Task 5 Step 2;§4.4 CLI → Task 3/5;§5 Ribbon 契约 → Task 1 Step 3 + Task 4 Step 4;§6 状态机与元素契约 → Task 2;§7 错误处理 → Task 3(端口/证书/Wef/Excel 检测)+ Task 5(删除失败提示);§8 验证 → Task 3/4/5;§10 交付物 → Task 1-6。无遗漏。
- **占位符**:无 TBD / TODO;每个代码步骤都给出完整可粘贴内容。
- **一致性**:`SIDELOAD_NAME`、`WEF_DIR`、`DEFAULT_PORT`、`MANIFEST_PORT_ANCHOR` 在 Task 3 定义、Task 5 复用同名常量;元素 id 在 Task 2 定义、Task 4/5 引用同一批字符串;端口 7300 在 manifest 与脚本中一致。

---

## 实施偏差记录(实施后回填)

计划里的以下内容在实施中被证伪或改进,最终实现以代码为准。

| 位置 | 计划原方案 | 实际实现 | 原因 |
|---|---|---|---|
| Task 1 Step 5 | 用 `bt:String` 的 `.text` 校验文案 | 改为读 `DefaultValue` 属性 | manifest 的 `bt:String` 用属性而非文本节点承载文案 |
| Task 2 `office.js` | `<script>` 同步加载 | 加 `async` + `taskpane.js` 内 3 秒有界等待 | 离线时 CDN 会阻塞整个面板渲染 |
| Task 3 证书链 | 只见 `Import-Certificate` | 改用 `certutil -user -addstore -f Root`,失败才回落 `Import-Certificate` | 非交互会话下 `Import-Certificate` 写 Root 会要求 UI 同意而报错 |
| Task 3 PowerShell 调用 | 直接继承环境变量 | 新增 `powershell_environment()`,把 `PSModulePath` 规范化为 Windows PowerShell 自己的路径 | 继承 PowerShell 7 的 `PSModulePath` 会让 `Microsoft.PowerShell.Security`/PKI 加载失败,`Cert:` 提供程序不存在 |
| Task 3 证书复用判断 | 只看 `CurrentUser\My` 是否有效 | 要求同一指纹也在 `CurrentUser\Root` | 否则会复用上一轮没进 Root 的证书,信任链断裂 |
| Task 3 TLS 材料 | `ssl.SSLContext.load_pkcs12` | 新增 `ensure_pem()`:openssl(`pkcs12 -nodes`,3.x 需 `-legacy`)优先、`pwsh` 的 .NET API 兜底,再 `load_cert_chain` | CPython 的 `SSLContext` 没有 `load_pkcs12` 这个 API |
| Task 3 CLI | 无 | 新增 `--prepare-only` | 需要一个有界、可重复执行的"只装不服务"入口,便于验收与非交互安装 |
| Task 4 浏览器验证 | agent-browser / 人工浏览器会话 | 自研零依赖 CDP 脚本 `verify/verify-flow.mjs`,自动断言 56 项并截图 | agent-browser 需联网下载 Chromium;本机已有 Chrome/Edge,Node 24 自带 `WebSocket`,零依赖更契合仓库风格 |
| Task 4 落点 | 仅 `verify-flow.mjs` 静态契约 | 静态契约 + 真实浏览器流程合并进同一脚本 | 一条命令即可完整验收 |
| Task 5 停服务 | `stop` 脚本"停服务" | 未实现停服务:服务在前台终端里用 Ctrl+C 结束 | 跨进程杀服务不可靠,文档已说明 |
| Task 5 Excel 侧验证 | 由脚本重启 Excel | 改为请用户手动重启 Excel 后再用 UIA 断言 | 用户当时有两个含真实工作簿的 Excel 进程在运行,不能强杀 |
| Task 6 | — | 新增本偏差记录 | 让计划与实现保持可追溯 |
| Task 3/5 sideload 机制 | 把 manifest 复制进 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` | 改为注册表开发者目录 `HKCU\SOFTWARE\Microsoft\Office\16.0\WEF\Developer\<插件Id> = manifest 绝对路径`(Wef 目录仍保留一份 manifest 副本) | **实测桌面版 Excel 不认"只拷 Wef 目录"**,重启后选项卡不出现;官方 `office-addin-dev-settings register` 写入的正是这个注册表项,且 manifest 已被官方校验器判定 `The manifest is valid.` |
| Task 5 卸载 | 只删 Wef 里的 manifest | 先删注册表项,再删 manifest 文件 | 注册表项才是 Excel 认的入口;另官方文档警告"不要只删单个 manifest 文件,可能导致所有加载项停止加载",已写进 README 故障排查 |
| Session 收尾 | — | 追加一次机制修正:第一次重启 Excel 时只有 Wef 拷贝,机制本身是错的,验证放到注册机制修好之后 | 避免把"机制错误"误判成"重装次数不够" |
