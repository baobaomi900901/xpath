# Virtual TreeView 5.5.3

上游：[JAM-Software/Virtual-TreeView](https://github.com/JAM-Software/Virtual-TreeView)。
此版本由上游明确列为支持 Delphi 7–XE2，包含 Delphi 2010。

下载地址：https://github.com/JAM-Software/Virtual-TreeView/releases/download/V5.5.3/VirtualTreeViewV5.5.3.zip

原始 ZIP SHA-256：`c0faf740c268644da835191071221c85fa69034039f85cc49b6eb5314f0a4970`

本目录保留运行时需要的 `VirtualTrees.pas`、`VirtualTrees.res`、`VTAccessibility.pas` 和 `VTAccessibilityFactory.pas`。
Pascal 文件仅将原始 Windows-1252 编码和 CRCRLF 换行统一为 UTF-8 BOM / CRLF，未修改控件逻辑。
无需安装 IDE 设计期包；构建脚本直接编译这些源码，静态链接到 EXE。

按上游源码声明，使用 Mozilla Public License 1.1，全文见 [LICENSE-MPL-1.1.txt](LICENSE-MPL-1.1.txt)。
源码中的原作者、贡献者和许可声明全部保留；这些源码随靶场一同提供。
