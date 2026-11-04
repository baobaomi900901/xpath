package com.xpath.shootingrange.ui;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.SwingUtilities;
import javax.swing.WindowConstants;
import javax.swing.table.DefaultTableModel;
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.GridBagLayout;

/** Standard JTable renderers whose virtual accessible cells can lack showing. */
public final class VirtualTableHitPanel extends JPanel {
    private final DefaultTableModel model = new DefaultTableModel(data(), columns()) {
        @Override
        public Class<?> getColumnClass(int column) {
            return column == 1 ? Boolean.class : String.class;
        }
    };
    private final JTable table = new JTable(model);

    public VirtualTableHitPanel() {
        this(true);
    }

    private VirtualTableHitPanel(boolean allowWindow) {
        setLayout(new BorderLayout(0, 12));
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));
        setName("virtual-table-hit-panel");
        add(buildInstructions(), BorderLayout.NORTH);

        table.setName("virtual-table-employees");
        table.getAccessibleContext().setAccessibleName("Employees");
        table.getTableHeader().setName("virtual-table-columns");
        table.getTableHeader().getAccessibleContext().setAccessibleName("Employee columns");
        table.setRowHeight(30);
        table.setPreferredScrollableViewportSize(new Dimension(450, 100));
        JScrollPane scroll = new JScrollPane(table);
        scroll.setColumnHeaderView(table.getTableHeader());
        JPanel stage = new JPanel(new GridBagLayout());
        stage.add(scroll);
        add(stage, BorderLayout.CENTER);
        add(buildActions(allowWindow), BorderLayout.SOUTH);
    }

    private JPanel buildInstructions() {
        JPanel instructions = new JPanel(new BorderLayout(0, 8));
        JLabel title = new JLabel("PR #31：虚拟表格单元格命中");
        title.setFont(title.getFont().deriveFont(Font.BOLD, 16f));
        instructions.add(title, BorderLayout.NORTH);
        instructions.add(new JLabel("<html>"
                + "使用 JAB 按坐标捕获单元格中心，优先打开新的独立复现窗口。<br>"
                + "文本格预期：label / same；勾选列预期：check box。<br>"
                + "异常：捕获到 table / Employees，高亮范围变为整张表。<br>"
                + "在鼠标尚未移入表格前捕获，以验证原生命中缺失时的补充遍历。<br>"
                + "虚拟单元格可能只有 visible、没有 showing，但仍显示在可见表格中。"
                + "</html>"), BorderLayout.CENTER);
        return instructions;
    }

    private JPanel buildActions(boolean allowWindow) {
        JPanel actions = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        JButton reset = new JButton("重置示例数据");
        reset.setName("virtual-table-reset");
        reset.addActionListener(event -> {
            if (table.isEditing()) table.getCellEditor().cancelCellEditing();
            model.setDataVector(data(), columns());
            table.clearSelection();
        });
        actions.add(reset);
        if (allowWindow) {
            JButton openWindow = new JButton("打开独立复现窗口");
            openWindow.setName("virtual-table-open-window");
            openWindow.addActionListener(event -> {
                JFrame window = new JFrame("Java 单元格命中复现 - PR #31");
                window.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
                window.setContentPane(new VirtualTableHitPanel(false));
                window.setMinimumSize(new Dimension(640, 440));
                window.pack();
                window.setLocationRelativeTo(SwingUtilities.getWindowAncestor(this));
                window.setVisible(true);
            });
            actions.add(openWindow);
        }
        return actions;
    }

    private static Object[][] data() {
        return new Object[][] {{"same", Boolean.TRUE, "same"}, {"same", Boolean.FALSE, "same"}};
    }

    private static Object[] columns() {
        return new Object[] {"ID", "Enabled", "Name"};
    }
}
