# Qt 多版本 RPA 靶场

依据用户已接受的 Qt 5.15 / 6.8、Widgets / QML 方向，参考 WIN32/README.md 的业务场景实现。

## 范围

- Qt 5.15.2、6.8.3，Windows x64，各构建 Widgets 和 Quick 两个程序。
- 十字段表单：姓名、密码、邮箱、年龄（18–80，初始25）、城市单选/多选、性别单选、兴趣多选、备注、协议。保存显示模态提交成功，重置恢复初值。
- 员工数据与 Win32 同算法：1000 条，7 列，20 条/页，50 页，首页/上一页/五个动态页码/下一页/末页。
- 拖拽目标120×80，限制区域内，记录位置、初始/本次位移、九宫格锚点、移动次数和耗时；隐藏后销毁目标、重置重新创建；复制与 Win32 相同字段顺序的 JSON。
- Qt 菜单和动态弹出菜单。Widgets 支持 grouped、flat、random 表单结构；随机布局和 objectName 在进程内固定，中文可访问名称不变。不把 Qt objectName 承诺为各版本一致的 Windows AutomationId。
- QML 使用 Qt Quick Controls 2 和 Accessible 元数据。保留原有 acc-hidden-profile 示例；不冒充纯 MSAA 或无内部树的全功能版本。

## 架构与取舍

选择共享 C++ 数据/拖拽模型 + 两套真实 UI；较只做 Widgets 覆盖更广，较每版本复制工程更容易保持一致。
版本清单固定 SDK/工具链；构建与 dist 按版本隔离，windeployqt 携带运行库和 QML 插件，启动清除 Qt 环境污染。
Python 标准库启动器接入 tools/ranges.json，支持多选、仅构建、已有产物、自检。
保留现有工作区其他改动，仅修改 Qt、Qt 启动入口和相关文档。

## 验收

两个真实 SDK 编译；QtTest 验证数据边界、拖拽、Widgets 的重置/分页/分组/随机、QML 加载与交互；程序可分别启动。启动器单测验证隔离、缺失依赖失败、参数和菜单；图像检查两种界面布局。部署目录离开 SDK PATH 仍可运行。
