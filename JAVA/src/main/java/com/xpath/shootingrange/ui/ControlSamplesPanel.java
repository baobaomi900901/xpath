package com.xpath.shootingrange.ui;

import javax.swing.*;
import java.awt.*;
import static com.xpath.shootingrange.ui.SamplePanelLayout.*;

/** Standard selection, text-state and numeric controls for manual automation. */
public final class ControlSamplesPanel extends JPanel {
    private static final String[] OPTIONS = {"北京", "上海", "广州", "同名", "同名"};
    private final JList<String> single = named(new JList<String>(OPTIONS), "示例单选列表");
    private final JList<String> multiple = named(new JList<String>(OPTIONS), "示例多选列表");
    private final JList<String> empty = named(new JList<String>(), "示例空列表");
    private final JTextField writable = named(new JTextField("可编辑内容"), "可编辑文本");
    private final JTextField readonly = named(new JTextField("只读内容"), "只读文本");
    private final JTextField disabled = named(new JTextField("禁用内容"), "禁用文本");
    private final JTextField hidden = named(new JTextField("显隐内容"), "显隐文本");
    private final JSlider slider = named(new JSlider(0, 100, 35), "示例滑块");
    private final JProgressBar progress = named(new JProgressBar(0, 100), "示例进度");
    private final JToggleButton toggle = named(new JToggleButton("示例开关"), "示例开关");
    private final JLabel selection = new JLabel();
    private final JLabel numeric = new JLabel();
    private final JLabel executions = new JLabel();
    private int executionCount;

    public ControlSamplesPanel() {
        super(new BorderLayout());
        single.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        multiple.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
        empty.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
        readonly.setEditable(false);
        JPanel lists = new JPanel(new GridLayout(1, 3, 10, 0));
        lists.add(list("单选列表", single));
        lists.add(list("多选列表", multiple));
        lists.add(list("空列表", empty));
        multiple.addListSelectionListener(event -> updateSelection());

        JPanel hiddenSlot = new JPanel(new BorderLayout());
        hiddenSlot.setPreferredSize(writable.getPreferredSize());
        hiddenSlot.add(hidden);
        JButton changeEnabled = new JButton("切换禁用状态");
        changeEnabled.addActionListener(event -> disabled.setEnabled(!disabled.isEnabled()));
        JButton changeVisible = new JButton("显示 / 隐藏输入");
        changeVisible.addActionListener(event -> { hidden.setVisible(!hidden.isVisible()); hiddenSlot.revalidate(); });

        slider.setMajorTickSpacing(25); slider.setPaintTicks(true); slider.setPaintLabels(true);
        progress.setStringPainted(true);
        slider.addChangeListener(event -> updateNumber());
        JButton execute = new JButton("执行一次");
        execute.addActionListener(event -> { executionCount++; updateExecutionCount(); });
        JTextArea longText = named(new JTextArea(longContent(), 6, 24), "长文本内容");
        longText.setEditable(false); longText.setLineWrap(true); longText.setWrapStyleWord(true);
        longText.setCaretPosition(0);

        JPanel cards = new JPanel(new GridLayout(2, 2, 12, 12));
        cards.add(card("列表选择", lists, selection, new JLabel("同名选项是两个独立项目，可分别选择。")));
        cards.add(card("文本状态", field("可编辑", writable), field("只读", readonly),
                field("禁用", disabled), field("显示 / 隐藏", hiddenSlot), row(changeEnabled, changeVisible)));
        cards.add(card("数值与操作", slider, progress, numeric, row(toggle, execute), executions));
        cards.add(card("长文本", new JLabel("包含中文、换行与表情，可滚动选择和复制。"),
                new JScrollPane(longText), new JLabel("字符数：" + longText.getText().length())));
        JButton reset = new JButton("重置选择与状态");
        reset.addActionListener(event -> reset());
        add(page(cards, row(reset)), BorderLayout.CENTER);
        reset();
    }

    private JPanel list(String caption, JList<String> list) {
        list.setVisibleRowCount(5);
        JPanel panel = new JPanel(new BorderLayout(0, 6));
        panel.add(new JLabel(caption), BorderLayout.NORTH);
        JScrollPane scroll = new JScrollPane(list);
        // Keep all five sample rows usable when GridBagLayout uses minimum sizes.
        scroll.setMinimumSize(new Dimension(70, scroll.getPreferredSize().height));
        panel.add(scroll, BorderLayout.CENTER);
        return panel;
    }

    private void reset() {
        single.setSelectedIndex(0); multiple.setSelectedIndices(new int[]{0, 1});
        empty.clearSelection(); writable.setText("可编辑内容"); readonly.setText("只读内容");
        disabled.setText("禁用内容"); disabled.setEnabled(false); hidden.setText("显隐内容"); hidden.setVisible(true);
        slider.setValue(35); toggle.setSelected(false); executionCount = 0;
        updateSelection(); updateNumber(); updateExecutionCount(); revalidate(); repaint();
    }

    private void updateSelection() { selection.setText("多选结果：" + String.join("、", multiple.getSelectedValuesList())); }
    private void updateNumber() { progress.setValue(slider.getValue()); numeric.setText("当前数值：" + slider.getValue()); }
    private void updateExecutionCount() { executions.setText("已执行：" + executionCount + " 次"); }
    private static String longContent() {
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < 360; i++) text.append("第 ").append(i + 1).append(" 行：中文与 Unicode 文本，表情 🙂，可以读取、选择和复制。\n");
        return text.toString();
    }
}
