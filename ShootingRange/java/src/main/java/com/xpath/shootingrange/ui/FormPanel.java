package com.xpath.shootingrange.ui;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JRadioButton;
import javax.swing.JScrollPane;
import javax.swing.JSpinner;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SpinnerNumberModel;
import javax.swing.ButtonGroup;
import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class FormPanel extends JPanel {
    private static final String[] CITIES = {"北京", "上海", "广州", "深圳", "杭州"};
    private static final String[] HOBBIES = {"阅读", "运动", "音乐", "旅行"};

    private final JTextField nameField = new JTextField(24);
    private final JPasswordField passwordField = new JPasswordField(24);
    private final JTextField emailField = new JTextField(24);
    private final JSpinner ageSpinner = new JSpinner(new SpinnerNumberModel(25, 18, 80, 1));
    private final JComboBox<String> cityCombo = new JComboBox<>(CITIES);
    private final JRadioButton maleRadio = new JRadioButton("男");
    private final JRadioButton femaleRadio = new JRadioButton("女");
    private final JRadioButton otherRadio = new JRadioButton("其他");
    private final Map<String, JCheckBox> hobbyBoxes = new LinkedHashMap<>();
    private final List<JCheckBox> cityMultiBoxes = new ArrayList<>();
    private final JTextArea remarkArea = new JTextArea(4, 24);
    private final JCheckBox agreeCheck = new JCheckBox("同意用户协议");

    public FormPanel() {
        setLayout(new BorderLayout(0, 12));
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));
        add(buildForm(), BorderLayout.CENTER);
        add(buildActions(), BorderLayout.SOUTH);
    }

    private JScrollPane buildForm() {
        JPanel form = new JPanel(new GridBagLayout());
        form.setBorder(BorderFactory.createTitledBorder("用户信息表单"));
        GridBagConstraints constraints = new GridBagConstraints();
        constraints.insets = new Insets(6, 8, 6, 8);
        constraints.anchor = GridBagConstraints.WEST;
        constraints.fill = GridBagConstraints.HORIZONTAL;
        constraints.weightx = 1;

        int row = 0;
        row = addField(form, constraints, row, "姓名", nameField);
        row = addField(form, constraints, row, "密码", passwordField);
        row = addField(form, constraints, row, "邮箱", emailField);
        row = addField(form, constraints, row, "年龄", ageSpinner);
        row = addField(form, constraints, row, "城市（单选）", cityCombo);
        row = addField(form, constraints, row, "城市（多选）", buildMultiCityPanel());
        row = addField(form, constraints, row, "性别（单选）", buildGenderPanel());
        row = addField(form, constraints, row, "兴趣爱好（多选）", buildHobbyPanel());
        row = addField(form, constraints, row, "备注", new JScrollPane(remarkArea));
        addField(form, constraints, row, "协议", agreeCheck);

        JScrollPane scrollPane = new JScrollPane(form);
        scrollPane.setBorder(BorderFactory.createEmptyBorder());
        return scrollPane;
    }

    private JPanel buildMultiCityPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        for (String city : CITIES) {
            JCheckBox checkBox = new JCheckBox(city);
            checkBox.setName("city-multi-" + city);
            cityMultiBoxes.add(checkBox);
            panel.add(checkBox);
        }
        return panel;
    }

    private JPanel buildGenderPanel() {
        ButtonGroup group = new ButtonGroup();
        group.add(maleRadio);
        group.add(femaleRadio);
        group.add(otherRadio);
        maleRadio.setSelected(true);

        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        panel.add(maleRadio);
        panel.add(femaleRadio);
        panel.add(otherRadio);
        return panel;
    }

    private JPanel buildHobbyPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        for (String hobby : HOBBIES) {
            JCheckBox checkBox = new JCheckBox(hobby);
            hobbyBoxes.put(hobby, checkBox);
            panel.add(checkBox);
        }
        return panel;
    }

    private JPanel buildActions() {
        JButton saveButton = new JButton("保存");
        saveButton.setName("form-save-button");
        saveButton.addActionListener(event -> JOptionPane.showMessageDialog(
                this,
                "提交成功！",
                "提示",
                JOptionPane.INFORMATION_MESSAGE
        ));

        JButton resetButton = new JButton("重置");
        resetButton.setName("form-reset-button");
        resetButton.addActionListener(event -> resetForm());

        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 16, 8));
        panel.add(saveButton);
        panel.add(resetButton);
        return panel;
    }

    private void resetForm() {
        nameField.setText("");
        passwordField.setText("");
        emailField.setText("");
        ageSpinner.setValue(25);
        cityCombo.setSelectedIndex(0);
        maleRadio.setSelected(true);
        femaleRadio.setSelected(false);
        otherRadio.setSelected(false);
        remarkArea.setText("");
        agreeCheck.setSelected(false);
        hobbyBoxes.values().forEach(box -> box.setSelected(false));
        cityMultiBoxes.forEach(box -> box.setSelected(false));
    }

    private int addField(JPanel form, GridBagConstraints constraints, int row, String label, Component field) {
        constraints.gridx = 0;
        constraints.gridy = row;
        constraints.weightx = 0;
        form.add(new JLabel(label), constraints);

        constraints.gridx = 1;
        constraints.weightx = 1;
        if (field instanceof JSpinner || field instanceof JComboBox<?>) {
            field.setPreferredSize(new Dimension(240, field.getPreferredSize().height));
        }
        form.add(field, constraints);
        return row + 1;
    }
}
