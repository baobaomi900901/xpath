# Acc Hidden Profile（Qt 5.15 靶场）

单窗口名片页，用于测试 Windows 元素指明 / Inspect 行为。

> 本机已安装：**Qt 5.15.2 + MinGW 8.1** → `D:\Qt`  
> （公开镜像无 5.15.14 LTS；5.15.2 对 `Accessible.ignored` 靶场足够。）

## 界面内容

- 头像（Image）
- 昵称（Text）
- 正文（Text）

## Accessibility 行为

| 元素 | UI tree |
|------|---------|
| 头像 | 不出现（`Accessible.ignored: true`） |
| 昵称 | 不出现（`Accessible.ignored: true`） |
| 正文 | 可见 |
| 窗口 | 可见 |

## 一键打包 + 运行

```powershell
cd D:\code\xpath\靶场\QT
.\run.ps1
```

只构建不启动：`.\build.ps1`  
跳过构建直接运行：`.\run.ps1 -SkipBuild`

## 验证

1. 启动程序
2. 打开 Inspect.exe 或你的指明程序
3. 确认 UI tree 中只有窗口和正文，没有头像、昵称
