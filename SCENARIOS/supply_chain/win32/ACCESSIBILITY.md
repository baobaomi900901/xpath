# 按需激活的 Win32 UIA / MSAA

本模块用于供应链场景 B（供应商报价管理），不修改仓库独立的 `WIN32/` 控件靶场。普通原生界面、文件对话框和业务线程仍使用原实现。`--obstacles` 控制业务控件何时创建；本无障碍模块控制 Provider 何时创建，两者独立。

## 静默的含义

应用只为拥有的 HWND 挂接轻量状态，首次有效无障碍请求前不创建应用 Provider、原生无障碍委托或整棵节点树，不主动调用 UiaRaise*/NotifyWinEvent。普通创建和绘制不触发 Provider 工厂。窗口和可见原生控件仍正常绘制。

Windows 可以为 HWND、标题栏、菜单等提供系统代理。把 WM_GETOBJECT 交给默认窗口过程也不会阻止系统代理出现。因此这里保证的是应用管理的 Provider 按需创建，不承诺 Windows 桌面树彻底没有此窗口或所有系统事件都消失。

Inspect / FlaUI 调用 ElementFromHandle、ElementFromPoint 或树导航时，本身已经发出有效请求。判断“首次请求之前是否静默”必须使用下述独立诊断计数；不能先用 Inspect 遍历，再要求对象仍未初始化。客户端调用 FindAll 后大量节点被访问，是显式枚举行为，应与根请求导致的提前创建区分。

## 请求、缓存与回收

- 仅处理 WM_GETOBJECT 的 UiaRootObjectId / OBJID_CLIENT，按32位对象ID比较，避免64位lParam符号扩展问题。其他对象ID走原窗口处理。
- 每个 HWND 独立维护状态、代次和节点缓存。根工厂受锁保护；节点构造函数不创建后代。标准控件的信息与动作按需复用其原生语义。
- 导航、子项访问和支持的 Pattern 才构造相关节点；列表按请求创建行/单元格，虚拟项遵守 ItemContainer / VirtualizedItem 的标准接口约定。
- UIA 的 HWND 根不再次枚举子 HWND，交给 Windows host 拼接窗口片段，避免重复树或循环；MSAA 仍独立支持子 HWND 枚举。表头项、行、单元格是所属片段内的惰性节点。
- 表格替换数据前调用 Invalidate，旧代次对象安全返回元素不可用，防止旧索引对应到新物料。引用尚未释放的 COM 对象保持存活，不直接强制删除。
- 空闲回收使用30秒的活动租期；普通查询也算活动。全局 UiaClientsAreListening 只反映事件订阅，不等于本窗口的客户端连接数，也不能证明 MSAA/查询客户端已退出。回收策略不能把false单独当成断开证据。
- UiaDisconnectProvider 必须在同步 SendMessage 处理以外执行，且不持有缓存锁。销毁和程序退出会退休对应代次；后续有效请求重新激活。

这是一种按访问与租期管理的回收方式，不能从 Windows API 获得“所有查询客户端刚刚退出”的精确回调。空闲超时后客户端若仍保留旧引用，应处理元素不可用并重新定位。

## 构建与开发者验证

在仓库根目录执行：

```powershell
python tools/start_supply_chain.py build
ctest --test-dir SCENARIOS/supply_chain/build/win32 -C Release --output-on-failure
python tools/start_supply_chain.py launch --skip-build --profile basic --no-browser
```

在使用 Inspect、UIAutoma 或 FlaUI 读取目标之前，先运行：

```powershell
$probe = '.\SCENARIOS\supply_chain\build\win32\Release\supplier-accessibility-probe.exe'
& $probe --mode stats
& $probe --mode uia-root
& $probe --mode uia-child
& $probe --mode msaa-root
& $probe --mode msaa-child
```

`stats` 只发送独立的诊断消息，不发送 WM_GETOBJECT，不激活 Provider。探针先校验协议标识，未挂接的任意窗口不会被误判为“全部计数为零”。可传 `--hwnd 0x...` 定位某个业务子窗口，每个 HWND 的计数独立。

探针会输出请求前、持有引用时、释放后的状态。`--hold-ms` 在探针线程保留引用；`--wait-idle-ms` 在释放后等待回收，例如：

```powershell
& $probe --mode uia-root --wait-idle-ms 32000
& $probe --mode stats
& $probe --mode uia-root
```

没有其他工具持续查询或订阅目标时，预期可以看到 retired_epochs 增加、active回到0；再次请求 activation_epochs / root_objects_created 增加。客户端持续访问会延长租期，其他监听工具也可能影响实际回收。

诊断消息为 `WM_APP + 0x3A`，WPARAM为字段：0 active、1当前存活节点、2累计创建节点、3累计根对象、4累计根激活次数、5退休次数、6当前代次、7应用主动事件数、8原生委托获取次数、9协议标识0xA11。探针字段名 `native_delegate_creations` 指成功调用 CreateStdAccessibleObject 的次数，不代表 Windows 内部独立对象分配次数。委托按调用获取并释放，不缓存原生子树。代次标识在全进程唯一，数值不等于单 HWND 激活次数。

计数为应用实现的计数，不包含 Windows 内部对象；字段7对应本模块从不主动发出树事件的策略。计数不是完整性能基准，不能据此声称原程序启动性能必然有显著提升。模块在第一次有效请求前不启动回收定时器，UIAutomationCore / OLEACC 采用延迟加载；系统控件可以独立加载这些系统组件。

## 代码位置与支持范围

| 文件 / 函数 | 作用 |
| --- | --- |
| `lazy_accessibility.cpp`：Attach / Subclass | 挂接每个 HWND 的元数据、过滤 WM_GETOBJECT、返回 UIA 或 MSAA 根 |
| Acquire / Provider 构造函数 | 锁内按代次及索引获取单个节点；构造函数不创建后代 |
| Navigate / FindItemByProperty / GetItem / Realize | 按需导航、查询虚拟行、读取单元格、滚动实现行 |
| Retire / DrainCleanup / CleanupProc | 退休旧代次、在同步消息栈外断开 UIA、空闲回收与停止定时器 |
| Delegate | 按调用复用标准控件的原生名称、值和动作 |
| `main.cpp`：control / fill / proc / wWinMain | 挂接控件及表头、重建数据前失效、COM 初始化和退出清理 |
| `lazy_accessibility_tests.cpp` | 原生生命周期、并发工厂、虚拟列表及交互回归 |
| `lazy_accessibility_probe.cpp` | 进程外 UIA / MSAA 客户端及不激活 Provider 的诊断查询 |
| `CMakeLists.txt` | Provider 库、系统链接依赖、延迟加载、探针及 CTest |

本模块为当前场景的 Button 提供 Invoke，Edit 提供 Value，ListView 提供 Grid / Selection / ItemContainer，列表行提供 SelectionItem / ScrollItem / VirtualizedItem，单元格提供 GridItem，表头项提供 Invoke。不支持的 Pattern 返回空；没有宣称实现所有原生控件的 Text / Table / RangeValue Pattern。公共生命周期函数在拥有窗口的 UI 线程调用，Provider 工厂、弱缓存和引用计数提供线程安全保护。

对照验收时，先运行 stats 观察零创建，再用 UIA/MSAA 根请求激活，最后枚举子项。不要把客户端主动 FindAll、Inspect 展开整树产生的节点归为应用预建。1000行的单元测试从一个根查找第900行，只新增一个行 Provider；访问该行某单元格才新增一个单元格 Provider。应用界面仍正常显示全部原生数据，惰性的是无障碍对象，并非隐藏业务内容。

受限开发沙箱可能使 Windows EXE 在进入main前报0xC0000142。请在普通桌面终端执行原生测试和探针，并与程序内部断言失败区分。

## Windows API 依据

- [WM_GETOBJECT：请求来源、对象ID及32位比较](https://learn.microsoft.com/en-us/windows/win32/winauto/wm-getobject)
- [默认处理与标准控件代理](https://learn.microsoft.com/en-us/windows/win32/winauto/handling-the-wm-getobject-message)
- [UiaClientsAreListening：事件订阅检测](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcoreapi/nf-uiautomationcoreapi-uiaclientsarelistening)
- [CreateStdAccessibleObject：复用标准控件语义](https://learn.microsoft.com/en-us/windows/win32/api/oleacc/nf-oleacc-createstdaccessibleobject)
- [ItemContainer 与 VirtualizedItem](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-implementingitemcontainer)
- [UiaDisconnectProvider：断开、旧引用与同步消息限制](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcoreapi/nf-uiautomationcoreapi-uiadisconnectprovider)
