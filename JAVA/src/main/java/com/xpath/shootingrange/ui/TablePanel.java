package com.xpath.shootingrange.ui;

import com.xpath.shootingrange.model.Employee;
import com.xpath.shootingrange.util.DataGenerator;
import com.xpath.shootingrange.util.ExcelUtil;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.filechooser.FileNameExtensionFilter;
import javax.swing.table.AbstractTableModel;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class TablePanel extends JPanel {
    private static final int PAGE_SIZE = 20;
    private static final String[] COLUMN_NAMES = {"ID", "姓名", "部门", "城市", "状态", "邮箱", "入职日期"};

    private final List<Employee> allRows = new ArrayList<>(DataGenerator.buildEmployees(1000));
    private int currentPage = 1;

    private final EmployeeTableModel tableModel = new EmployeeTableModel();
    private final JTable table = new JTable(tableModel);
    private final JLabel pageInfoLabel = new JLabel();
    private final JPanel pageButtonsPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 4, 0));

    public TablePanel() {
        setLayout(new BorderLayout(0, 12));
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));

        table.setAutoCreateRowSorter(true);
        table.setRowHeight(28);
        table.setFillsViewportHeight(true);

        add(buildToolbar(), BorderLayout.NORTH);
        add(new JScrollPane(table), BorderLayout.CENTER);
        add(buildPagination(), BorderLayout.SOUTH);

        refreshPage();
    }

    private JPanel buildToolbar() {
        JButton importButton = new JButton("导入 Excel");
        importButton.setName("table-import-button");
        importButton.addActionListener(event -> importExcel());

        JButton exportButton = new JButton("导出 Excel");
        exportButton.setName("table-export-button");
        exportButton.addActionListener(event -> exportExcel());

        JLabel summary = new JLabel("共 " + allRows.size() + " 条数据，每页 " + PAGE_SIZE + " 条");

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(summary, BorderLayout.WEST);
        JPanel actions = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        actions.add(importButton);
        actions.add(exportButton);
        panel.add(actions, BorderLayout.EAST);
        return panel;
    }

    private JPanel buildPagination() {
        JButton firstButton = new JButton("首页");
        JButton prevButton = new JButton("上一页");
        JButton nextButton = new JButton("下一页");
        JButton lastButton = new JButton("末页");

        firstButton.addActionListener(event -> goToPage(1));
        prevButton.addActionListener(event -> goToPage(currentPage - 1));
        nextButton.addActionListener(event -> goToPage(currentPage + 1));
        lastButton.addActionListener(event -> goToPage(getTotalPages()));

        JPanel panel = new JPanel(new BorderLayout(8, 8));
        JPanel nav = new JPanel(new FlowLayout(FlowLayout.CENTER, 8, 0));
        nav.add(firstButton);
        nav.add(prevButton);
        nav.add(pageButtonsPanel);
        nav.add(nextButton);
        nav.add(lastButton);

        panel.add(nav, BorderLayout.CENTER);
        panel.add(pageInfoLabel, BorderLayout.SOUTH);
        return panel;
    }

    private void refreshPage() {
        int totalPages = getTotalPages();
        if (currentPage > totalPages) {
            currentPage = totalPages;
        }
        if (currentPage < 1) {
            currentPage = 1;
        }

        int start = (currentPage - 1) * PAGE_SIZE;
        int end = Math.min(start + PAGE_SIZE, allRows.size());
        tableModel.setRows(allRows.subList(start, end));

        rebuildPageButtons(totalPages);
        pageInfoLabel.setText("第 " + currentPage + " / " + totalPages + " 页，当前显示 "
                + (allRows.isEmpty() ? 0 : start + 1) + " - " + end + " 条");
    }

    private void rebuildPageButtons(int totalPages) {
        pageButtonsPanel.removeAll();
        int windowStart = Math.max(1, currentPage - 2);
        int windowEnd = Math.min(totalPages, currentPage + 2);

        if (windowStart > 1) {
            pageButtonsPanel.add(createPageButton(1));
            if (windowStart > 2) {
                pageButtonsPanel.add(new JLabel("..."));
            }
        }

        for (int page = windowStart; page <= windowEnd; page++) {
            pageButtonsPanel.add(createPageButton(page));
        }

        if (windowEnd < totalPages) {
            if (windowEnd < totalPages - 1) {
                pageButtonsPanel.add(new JLabel("..."));
            }
            pageButtonsPanel.add(createPageButton(totalPages));
        }

        pageButtonsPanel.revalidate();
        pageButtonsPanel.repaint();
    }

    private JButton createPageButton(int page) {
        JButton button = new JButton(String.valueOf(page));
        button.setEnabled(page != currentPage);
        button.addActionListener(event -> goToPage(page));
        return button;
    }

    private void goToPage(int page) {
        int totalPages = getTotalPages();
        if (page < 1 || page > totalPages) {
            return;
        }
        currentPage = page;
        refreshPage();
    }

    private int getTotalPages() {
        if (allRows.isEmpty()) {
            return 1;
        }
        return (allRows.size() + PAGE_SIZE - 1) / PAGE_SIZE;
    }

    private void importExcel() {
        JFileChooser chooser = new JFileChooser();
        chooser.setDialogTitle("选择 Excel 文件");
        chooser.setFileFilter(new FileNameExtensionFilter("Excel 文件 (*.xlsx)", "xlsx"));
        if (chooser.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) {
            return;
        }

        Path file = chooser.getSelectedFile().toPath();
        try {
            List<Employee> imported = ExcelUtil.importEmployees(file);
            allRows.clear();
            allRows.addAll(imported);
            currentPage = 1;
            refreshPage();
            JOptionPane.showMessageDialog(this, "成功导入 " + imported.size() + " 条数据", "导入成功",
                    JOptionPane.INFORMATION_MESSAGE);
        } catch (IOException | RuntimeException ex) {
            JOptionPane.showMessageDialog(this, "导入失败：" + ex.getMessage(), "错误",
                    JOptionPane.ERROR_MESSAGE);
        }
    }

    private void exportExcel() {
        JFileChooser chooser = new JFileChooser();
        chooser.setDialogTitle("导出 Excel 文件");
        chooser.setSelectedFile(new java.io.File("员工数据.xlsx"));
        chooser.setFileFilter(new FileNameExtensionFilter("Excel 文件 (*.xlsx)", "xlsx"));
        if (chooser.showSaveDialog(this) != JFileChooser.APPROVE_OPTION) {
            return;
        }

        Path file = chooser.getSelectedFile().toPath();
        if (!file.toString().toLowerCase().endsWith(".xlsx")) {
            file = file.resolveSibling(file.getFileName() + ".xlsx");
        }

        try {
            ExcelUtil.exportEmployees(file, allRows);
            JOptionPane.showMessageDialog(this, "已导出到：\n" + file, "导出成功",
                    JOptionPane.INFORMATION_MESSAGE);
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "导出失败：" + ex.getMessage(), "错误",
                    JOptionPane.ERROR_MESSAGE);
        }
    }

    private static final class EmployeeTableModel extends AbstractTableModel {
        private List<Employee> pageRows = Collections.emptyList();

        void setRows(List<Employee> rows) {
            this.pageRows = rows;
            fireTableDataChanged();
        }

        @Override
        public int getRowCount() {
            return pageRows.size();
        }

        @Override
        public int getColumnCount() {
            return COLUMN_NAMES.length;
        }

        @Override
        public String getColumnName(int column) {
            return COLUMN_NAMES[column];
        }

        @Override
        public Object getValueAt(int rowIndex, int columnIndex) {
            Employee employee = pageRows.get(rowIndex);
            switch (columnIndex) {
                case 0:
                    return employee.id();
                case 1:
                    return employee.name();
                case 2:
                    return employee.department();
                case 3:
                    return employee.city();
                case 4:
                    return employee.status();
                case 5:
                    return employee.email();
                case 6:
                    return employee.joinDate();
                default:
                    return "";
            }
        }
    }
}
