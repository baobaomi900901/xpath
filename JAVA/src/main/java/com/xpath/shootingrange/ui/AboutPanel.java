package com.xpath.shootingrange.ui;

import javax.swing.BorderFactory;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JEditorPane;
import javax.swing.UIManager;
import java.awt.BorderLayout;

public class AboutPanel extends JPanel {
    public AboutPanel() {
        setLayout(new BorderLayout());
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));

        JEditorPane content = new JEditorPane("text/html", buildHtml());
        content.setEditable(false);
        content.setBorder(BorderFactory.createEmptyBorder());
        content.putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, Boolean.TRUE);
        content.setCaretPosition(0);

        JScrollPane scrollPane = new JScrollPane(content);
        scrollPane.setBorder(BorderFactory.createTitledBorder("关于 Java 靶场"));
        add(scrollPane, BorderLayout.CENTER);
    }

    private static String buildHtml() {
        String javaVersion = System.getProperty("java.version", "未知");
        String javaVendor = System.getProperty("java.vendor", "未知");
        String javaHome = System.getProperty("java.home", "未知");
        String jvmName = System.getProperty("java.vm.name", "未知");
        String osName = System.getProperty("os.name", "未知");
        String osArch = System.getProperty("os.arch", "未知");
        String osVersion = System.getProperty("os.version", "未知");
        String lookAndFeel = getLookAndFeelName();
        String fileEncoding = System.getProperty("file.encoding", "未知");

        String html = "<html>"
                + "<body style='font-family: Segoe UI, Microsoft YaHei, sans-serif; font-size: 14px; line-height: 1.6; color: #1f2937;'>"
                + "<h2 style='margin-top: 0;'>Java 靶场</h2>"
                + "<p>本程序是基于 <b>Java Swing</b> 的桌面 UI 自动化测试靶场，用于练习元素定位、表单操作、表格分页与文件对话框等场景。</p>"
                + "<h3>当前运行环境</h3>"
                + "<table cellpadding='4' cellspacing='0' style='border-collapse: collapse;'>"
                + "<tr><td style='color:#64748b;'>Java 版本</td><td><b>%s</b></td></tr>"
                + "<tr><td style='color:#64748b;'>JVM</td><td>%s</td></tr>"
                + "<tr><td style='color:#64748b;'>供应商</td><td>%s</td></tr>"
                + "<tr><td style='color:#64748b;'>JAVA_HOME</td><td>%s</td></tr>"
                + "<tr><td style='color:#64748b;'>Look &amp; Feel</td><td>%s</td></tr>"
                + "<tr><td style='color:#64748b;'>操作系统</td><td>%s (%s)</td></tr>"
                + "<tr><td style='color:#64748b;'>系统版本</td><td>%s</td></tr>"
                + "<tr><td style='color:#64748b;'>文件编码</td><td>%s</td></tr>"
                + "</table>"
                + "<h3>可能影响 UI 识别的因素</h3>"
                + "<p>Java Swing 程序通常通过 <b>Java Access Bridge (JAB)</b> 或 Windows UI Automation 暴露可访问性树。以下情况可能导致定位失败或结果不一致：</p>"
                + "<ul>"
                + "<li><b>Java Access Bridge 未启用</b>：需在「控制面板 → 轻松使用 → 使计算机更易于查看 → 启用 Java Access Bridge」或安装对应 JAB 组件，否则 Inspect/自动化工具可能看不到 Swing 控件。</li>"
                + "<li><b>Look &amp; Feel 差异</b>：当前使用系统 L&amp;F（Windows 风格）。切换为 Metal、Nimbus 等主题时，控件层级与 accessible name 可能变化。</li>"
                + "<li><b>组件 name 属性</b>：部分控件设置了 <code>setName()</code>（如保存/重置、导入/导出按钮），可作为稳定锚点；未设置 name 的控件需依赖 label 文本或坐标定位。</li>"
                + "<li><b>模态对话框</b>：「保存」按钮会弹出 <code>JOptionPane</code> 模态框，自动化需先处理对话框再操作主窗口；对话框不在 Tab 内容区内。</li>"
                + "<li><b>Tab 切换</b>：表单、表格、关于页在 <code>JTabbedPane</code> 中，未激活 Tab 内的控件通常不可见或不可交互，需先切换 Tab。</li>"
                + "<li><b>表格分页</b>：表格 Tab 仅渲染当前页 20 条数据，共 1000 条；翻页后行内容与行号变化，勿用固定行索引跨页定位。</li>"
                + "<li><b>文件选择对话框</b>：导入/导出 Excel 会弹出原生 <code>JFileChooser</code>，属于独立窗口，与主窗口 accessibility 树分离。</li>"
                + "<li><b>密码框</b>：密码字段为 <code>JPasswordField</code>，部分工具对 echo 字符的处理与普通文本框不同。</li>"
                + "<li><b>Spinner / ComboBox</b>：下拉与微调控件的可访问性名称可能不包含当前选中值，需通过键盘或展开后选择。</li>"
                + "<li><b>高 DPI / 缩放</b>：Windows 显示缩放非 100%% 时，坐标点击可能偏移；建议优先用语义定位而非纯坐标。</li>"
                + "<li><b>多选 Checkbox 组</b>：城市多选、兴趣爱好等多选框为独立控件，「全选/半选」状态需逐个判断 checked 属性。</li>"
                + "</ul>"
                + "<h3>各 Tab 说明</h3>"
                + "<ul>"
                + "<li><b>表单控件</b>：输入框、下拉、单选、多选、保存/重置与成功提示。</li>"
                + "<li><b>表格数据</b>：1000 条数据、分页器、Excel 导入导出。</li>"
                + "<li><b>关于</b>：本页，环境与识别注意事项。</li>"
                + "</ul>"
                + "</body>"
                + "</html>";

        return String.format(html,
                escape(javaVersion),
                escape(jvmName),
                escape(javaVendor),
                escape(javaHome),
                escape(lookAndFeel),
                escape(osName),
                escape(osArch),
                escape(osVersion),
                escape(fileEncoding)
        );
    }

    private static String getLookAndFeelName() {
        try {
            return UIManager.getLookAndFeel().getName()
                    + " (" + UIManager.getLookAndFeel().getClass().getSimpleName() + ")";
        } catch (Exception ex) {
            return "未知";
        }
    }

    private static String escape(String value) {
        return value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;");
    }
}
