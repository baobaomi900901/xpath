package com.xpath.shootingrange.ui;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import java.awt.*;
import static com.xpath.shootingrange.ui.SamplePanelLayout.*;

/** Repeatable object replacement, sibling scope, mixed table and tree samples. */
public final class DynamicSamplesPanel extends JPanel {
    private final JPanel inputHost = named(new JPanel(new BorderLayout()), "动态输入容器");
    private final JPanel choices = named(new JPanel(new GridLayout(0, 2, 8, 6)), "动态选项组");
    private final JTable table = named(new JTable(), "混合数据表格");
    private final JTree tree = named(new JTree(), "示例树");
    private final JLabel inputStatus = new JLabel();
    private final JLabel tableStatus = new JLabel();
    private int inputVersion;
    private int tableVersion;
    private int treeSequence;

    public DynamicSamplesPanel() {
        super(new BorderLayout());
        JButton replaceInput = new JButton("替换输入对象");
        replaceInput.addActionListener(event -> replaceInput());
        JButton addChoice = new JButton("增加同名项");
        addChoice.addActionListener(event -> { choices.add(new JCheckBox("动态选项")); refreshChoices(); });
        JButton removeChoice = new JButton("移除首项");
        removeChoice.addActionListener(event -> { if (choices.getComponentCount() > 0) choices.remove(0); refreshChoices(); });
        JButton replaceChoice = new JButton("替换首项");
        replaceChoice.addActionListener(event -> {
            if (choices.getComponentCount() == 0) return;
            boolean checked = ((JCheckBox) choices.getComponent(0)).isSelected();
            choices.remove(0); choices.add(new JCheckBox("动态选项", checked), 0); refreshChoices();
        });
        JPanel neighbor = named(new JPanel(new FlowLayout(FlowLayout.LEFT)), "相邻选项组");
        neighbor.add(new JCheckBox("动态选项"));
        JScrollPane choiceScroll = new JScrollPane(choices);
        choiceScroll.setPreferredSize(new Dimension(300, 55));

        table.setAutoCreateRowSorter(true); table.setRowHeight(26);
        table.setPreferredScrollableViewportSize(new Dimension(300, 108));
        JButton replaceModel = new JButton("替换表格模型");
        replaceModel.addActionListener(event -> replaceModel());
        JButton sort = new JButton("切换排序");
        sort.addActionListener(event -> table.getRowSorter().toggleSortOrder(0));
        tree.setRowHeight(24); tree.setVisibleRowCount(5);
        JButton addNode = new JButton("添加树节点");
        addNode.addActionListener(event -> {
            DefaultTreeModel model = (DefaultTreeModel) tree.getModel();
            DefaultMutableTreeNode root = (DefaultMutableTreeNode) model.getRoot();
            model.insertNodeInto(new DefaultMutableTreeNode("新增成员 " + (++treeSequence)), root, root.getChildCount());
            tree.expandRow(0);
        });
        JPanel cards = new JPanel(new GridLayout(2, 2, 12, 12));
        cards.add(card("输入对象", new JLabel("替换后名称和内容相同，对象会重新创建。"), inputHost, row(replaceInput), inputStatus));
        cards.add(card("同名选项与相邻分组", choiceScroll, row(addChoice, removeChoice, replaceChoice),
                field("相邻分组", neighbor)));
        cards.add(card("混合表格", new JScrollPane(table), row(replaceModel, sort), tableStatus));
        cards.add(card("树节点", new JScrollPane(tree), row(addNode)));
        JButton reset = new JButton("重置动态样本");
        reset.addActionListener(event -> { ((JCheckBox) neighbor.getComponent(0)).setSelected(false); reset(); });
        add(page(cards, row(reset)), BorderLayout.CENTER);
        reset();
    }

    private void replaceInput() {
        inputHost.removeAll(); inputHost.add(named(new JTextField("相同内容"), "动态输入"));
        inputStatus.setText("输入对象版本：" + (++inputVersion)); inputHost.revalidate(); inputHost.repaint();
    }
    private void refreshChoices() { choices.revalidate(); choices.repaint(); }
    private void replaceModel() {
        table.setModel(new DefaultTableModel(new Object[][]{{3, "同名", true}, {1, "同名", false}, {2, "样本", true}},
                new Object[]{"ID", "名称", "启用"}) {
            public Class<?> getColumnClass(int column) { return column == 0 ? Integer.class : column == 2 ? Boolean.class : String.class; }
            public boolean isCellEditable(int row, int column) { return column == 2; }
        });
        tableStatus.setText("表格模型版本：" + (++tableVersion));
    }
    private void reset() {
        inputVersion = 0; tableVersion = 0; treeSequence = 0;
        replaceInput(); replaceModel(); choices.removeAll();
        for (int i = 0; i < 3; i++) choices.add(new JCheckBox("动态选项"));
        refreshChoices();
        DefaultMutableTreeNode root = new DefaultMutableTreeNode("示例组织");
        DefaultMutableTreeNode development = new DefaultMutableTreeNode("研发部");
        development.add(new DefaultMutableTreeNode("北京办公室")); development.add(new DefaultMutableTreeNode("上海办公室"));
        root.add(development); root.add(new DefaultMutableTreeNode("支持部"));
        tree.setModel(new DefaultTreeModel(root));
        for (int i = 0; i < tree.getRowCount(); i++) tree.expandRow(i);
    }
}
