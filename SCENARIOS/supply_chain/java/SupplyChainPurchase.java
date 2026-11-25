import javax.swing.*;
import javax.swing.table.*;
import javax.swing.event.*;
import java.awt.*;
import java.io.*;
import java.net.*;
import java.math.*;
import java.time.LocalDate;
import java.util.*;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.function.Consumer;
import java.util.function.BooleanSupplier;

/** Genuine Swing purchase entry client; Java 8 and standard library only. */
public class SupplyChainPurchase {
    final String base;
    final JFrame frame = new JFrame("采购管理 — 库存补货任务");
    final JLabel status = new JLabel("正在加载任务信息…");
    JLabel amount;
    JTextField batch, warehouse, date, supplier;
    JTextArea notes, reason;
    JTextField exceptionMaterial;
    final DefaultTableModel lines = new DefaultTableModel(new String[] {
        "物料编码", "数量", "含税单价", "报价编号"
    }, 0);
    JTable lineTable;
    final DefaultTableModel orders = new DefaultTableModel(new String[] {
        "订单号", "批次", "供应商编码", "供应商", "仓库", "交货日期", "金额", "状态", "明细"
    }, 0) {
        public boolean isCellEditable(int r, int c) {
            return false;
        }
    };
    JButton submit, exceptionSubmit;
    final JButton reloadContext = new JButton("重新加载任务信息");
    final RequestGeneration orderRefreshes = new RequestGeneration();
    boolean contextLoaded = false;
    final boolean obstacles;
    final TaskContext context = new TaskContext();
    final List<LazyPage> lazyPages = new ArrayList<LazyPage>();

    static final class TaskContext {
        private Map<String, String> values = new HashMap<String, String>();
        private JTextField batch, warehouse, date;
        void accept(Map<String, String> next) {
            values = new HashMap<String, String>(next);
            apply();
        }
        void bind(JTextField b, JTextField w, JTextField d) {
            batch = b; warehouse = w; date = d; apply();
        }
        void apply() {
            if (batch == null || values.isEmpty()) return;
            batch.setText(values.get("batch_id")); warehouse.setText(values.get("warehouse")); date.setText(values.get("deadline"));
        }
        String batchId() { return values.get("batch_id"); }
    }

    /** Created on the EDT; factory does not run until the one-shot timer fires. */
    static final class LazyPage extends JPanel {
        final javax.swing.Timer timer;
        final java.util.function.Supplier<JComponent> factory;
        final JLabel loading;
        JComponent content;
        boolean requested, closed;
        LazyPage(String title, java.util.function.Supplier<JComponent> factory) {
            super(new BorderLayout());
            this.factory = factory;
            loading = named(new JLabel("选择页签后加载" + title, SwingConstants.CENTER), title + "加载状态");
            add(loading);
            timer = new javax.swing.Timer(1200, e -> finish());
            timer.setRepeats(false);
        }
        void request() {
            if (closed || requested || content != null) return;
            requested = true;
            loading.setText("正在加载页面，请稍候…");
            timer.start();
        }
        void finish() {
            timer.stop();
            if (closed || !requested || content != null) return;
            content = factory.get();
            removeAll(); add(content); revalidate(); repaint();
            if (isShowing()) content.transferFocus();
        }
        void close() { closed = true; timer.stop(); }
    }

    /** Accessed on the EDT; only the newest request may publish its result. */
    static final class RequestGeneration {
        private long latest;

        long begin() {
            return ++latest;
        }

        boolean isCurrent(long request) {
            return request == latest;
        }
    }

    /** DefaultTableModel keeps a distinct Vector identity for every inserted row. */
    static int rowIndex(DefaultTableModel model, Object identity) {
        for (int i = 0; i < model.getRowCount(); i++) {
            if (model.getDataVector().get(i) == identity) return i;
        }
        return -1;
    }

    public SupplyChainPurchase(String base) { this(base, false); }

    public SupplyChainPurchase(String base, boolean obstacles) {
        this.obstacles = obstacles;
        this.base = base.replaceAll("/+$", "");
        build();
        loadContext();
        refreshOrders();
    }

    static JTextField field(String name) {
        JTextField f = new JTextField(22);
        f.getAccessibleContext().setAccessibleName(name);
        return f;
    }

    static <T extends JComponent> T named(T c, String name) {
        c.getAccessibleContext().setAccessibleName(name);
        return c;
    }

    static JPanel row(Object... items) {
        JPanel p = new JPanel(new FlowLayout(FlowLayout.LEFT));
        for (Object x : items) p.add(x instanceof Component ? (Component) x : new JLabel(x.toString()));
        return p;
    }

    JButton button(String title, Runnable run) {
        JButton b = named(new JButton(title), title);
        b.addActionListener(e -> run.run());
        return b;
    }

    void build() {
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.getAccessibleContext().setAccessibleName("采购管理客户端");
        JTabbedPane tabs = named(new JTabbedPane(), "采购业务页签");
        addPage(tabs, "订单列表", () -> buildOrders());
        addPage(tabs, "新建采购单", () -> buildCreate());
        addPage(tabs, "异常登记", () -> buildExceptions());
        if (obstacles) {
            tabs.addChangeListener(e -> ((LazyPage) tabs.getSelectedComponent()).request());
            ((LazyPage) tabs.getSelectedComponent()).request();
            frame.addWindowListener(new java.awt.event.WindowAdapter() {
                public void windowClosing(java.awt.event.WindowEvent e) { for (LazyPage page : lazyPages) page.close(); }
                public void windowClosed(java.awt.event.WindowEvent e) { for (LazyPage page : lazyPages) page.close(); }
            });
        }
        named(reloadContext, "重新加载任务信息");
        reloadContext.addActionListener(e -> loadContext());
        frame.add(row(reloadContext), BorderLayout.NORTH);
        frame.add(tabs);
        frame.add(named(status, "业务状态"), BorderLayout.SOUTH);
        frame.setSize(1080, 720);
        frame.setLocationByPlatform(true);
        frame.setVisible(true);
    }

    void addPage(JTabbedPane tabs, String title, java.util.function.Supplier<JComponent> factory) {
        if (obstacles) {
            LazyPage page = new LazyPage(title, factory);
            lazyPages.add(page); tabs.add(title, page);
        } else tabs.add(title, factory.get());
    }

    JPanel buildOrders() {
        JTable orderTable = named(new JTable(orders), "采购订单回查列表");
        orderTable.setAutoCreateRowSorter(true);
        orderTable.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
        for (int i = 0; i < orders.getColumnCount(); i++) orderTable.getColumnModel().getColumn(i).setPreferredWidth(i == 8 ? 440 : 140);
        JPanel list = new JPanel(new BorderLayout());
        list.add(row(button("刷新订单", () -> refreshOrders())), BorderLayout.NORTH);
        list.add(new JScrollPane(orderTable));
        return list;
    }

    JPanel buildCreate() {
        batch = field("任务批次"); warehouse = field("收货仓库"); date = field("交货日期 YYYY-MM-DD"); supplier = field("供应商编码");
        notes = new JTextArea(3, 40); lineTable = new JTable(lines);
        amount = new JLabel("合计：0.00 元"); submit = new JButton("提交采购单");
        JPanel create = new JPanel(new BorderLayout(8, 8)), headers = new JPanel();
        headers.setLayout(new BoxLayout(headers, BoxLayout.Y_AXIS));
        headers.add(row("批次", batch, "仓库", warehouse));
        headers.add(row("供应商", supplier, button("选择供应商", () -> choose("供应商", "/api/suppliers?format=tsv", new String[] {
            "supplier_id", "name", "active"
        }, new String[] {
            "供应商编码", "名称", "启用"
        }, r -> supplier.setText(r.get("supplier_id"))))));
        headers.add(row("交货日期", date, "格式：YYYY-MM-DD"));
        create.add(headers, BorderLayout.NORTH);
        named(lineTable, "采购明细可编辑表格");
        lineTable.putClientProperty("terminateEditOnFocusLost", Boolean.TRUE);
        lineTable.setRowHeight(26);
        lineTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        create.add(new JScrollPane(lineTable));
        JPanel bottom = new JPanel();
        bottom.setLayout(new BoxLayout(bottom, BoxLayout.Y_AXIS));
        bottom.add(row(button("增加明细", () -> lines.addRow(new String[] {
            "", "", "", ""
        })), button("删除明细", () -> {
            int r = lineTable.getSelectedRow();
            if (r >= 0) lines.removeRow(r);
        }), button("选择明细物料", () -> chooseMaterial()), amount));
        named(notes, "采购备注");
        bottom.add(row("备注", new JScrollPane(notes)));
        named(submit, "提交采购单");
        submit.addActionListener(e -> submitOrder());
        bottom.add(row(submit));
        create.add(bottom, BorderLayout.SOUTH);
        lines.addTableModelListener(e -> updateAmount());
        lines.addRow(new String[] { "", "", "", "" });
        context.bind(batch, warehouse, date);
        return create;
    }

    JPanel buildExceptions() {
        exceptionMaterial = field("异常物料编码"); reason = new JTextArea(5, 40); exceptionSubmit = new JButton("登记异常");
        JPanel exceptions = new JPanel();
        exceptions.setLayout(new BoxLayout(exceptions, BoxLayout.Y_AXIS));
        exceptions.add(row("物料编码", exceptionMaterial, button("选择异常物料", () -> choose("物料", "/api/materials?format=tsv",
        new String[] {
            "material_id", "name", "unit"
        }, new String[] {
            "物料编码", "物料名称", "单位"
        }, r -> exceptionMaterial.setText(r.get("material_id"))))));
        named(reason, "异常原因");
        exceptions.add(row("异常原因", new JScrollPane(reason)));
        exceptionSubmit.addActionListener(e -> submitException());
        named(exceptionSubmit, "登记异常");
        exceptions.add(row(exceptionSubmit));
        return exceptions;
    }

    void loadContext() {
        reloadContext.setEnabled(false);
        async("加载任务信息", () -> parseTsv(request("GET", "/api/context?format=tsv", null)), rows -> {
            if (rows.isEmpty()) throw new IllegalArgumentException("任务信息为空");
            Map<String, String> c = rows.get(0);
            context.accept(c);
            contextLoaded = true;
            status.setText("业务日期：" + c.get("today") + "；截止日期：" + c.get("deadline") + "；批次：" + c.get("batch_id"));
        }, () -> reloadContext.setEnabled(true));
    }

    void refreshOrders() {
        final long generation = orderRefreshes.begin();
        async("查询订单", () -> parseTsv(request("GET", "/api/orders?format=tsv", null)), rows -> {
            orders.setRowCount(0);
            String[] keys = {
                "order_id", "batch_id", "supplier_id", "supplier_name", "warehouse", "delivery_date", "total",
                "status", "lines"
            };
            for (Map<String, String> r : rows) {
                Object[] v = new Object[keys.length];
                for (int i = 0; i < keys.length; i++) v[i] = r.get(keys[i]);
                orders.addRow(v);
            }
            status.setText("已回查订单 " + rows.size() + " 条");
        }, () -> {}, () -> orderRefreshes.isCurrent(generation));
    }

    void choose(String title, String path, String[] keys, String[] labels, Consumer<Map<String, String>> apply) {
        async("查询" + title, () -> parseTsv(request("GET", path, null)), rows -> {
            JDialog dialog = new JDialog(frame, "选择" + title, true);
            dialog.getAccessibleContext().setAccessibleName("选择" + title + "对话框");
            DefaultTableModel model = new DefaultTableModel(labels, 0) {
                public boolean isCellEditable(int r, int c) {
                    return false;
                }
            };
            for (Map<String, String> r : rows) {
                Object[] v = new Object[keys.length];
                for (int i = 0; i < keys.length; i++) v[i] = r.get(keys[i]);
                model.addRow(v);
            }
            JTable table = named(new JTable(model), title + "选择列表");
            table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            table.setAutoCreateRowSorter(true);
            JTextField filter = field(title + "查询关键字");
            javax.swing.table.TableRowSorter<TableModel> sorter = new javax.swing.table.TableRowSorter<TableModel>(model);
            table.setRowSorter(sorter);
            filter.getDocument().addDocumentListener(new DocumentListener() {
                void change() {
                    sorter.setRowFilter(RowFilter.regexFilter("(?i)" + java.util.regex.Pattern.quote(filter.getText())));
                }
                public void insertUpdate(DocumentEvent e) {
                    change();
                }
                public void removeUpdate(DocumentEvent e) {
                    change();
                }
                public void changedUpdate(DocumentEvent e) {
                    change();
                }
            });
            dialog.add(row("关键字", filter), BorderLayout.NORTH);
            dialog.add(new JScrollPane(table));
            dialog.add(row(button("确定选择", () -> {
                int i = table.getSelectedRow();
                if (i < 0) {
                    JOptionPane.showMessageDialog(dialog, "请选择一行");
                    return;
                }
                apply.accept(rows.get(table.convertRowIndexToModel(i)));
                dialog.dispose();
            }), button("取消", () -> dialog.dispose())), BorderLayout.SOUTH);
            dialog.setSize(650, 440);
            dialog.setLocationRelativeTo(frame);
            dialog.setVisible(true);
        });
    }

    void chooseMaterial() {
        if (lineTable.isEditing()) lineTable.getCellEditor().stopCellEditing();
        int selected = lineTable.getSelectedRow();
        if (selected < 0) {
            lines.addRow(new String[] {
                "", "", "", ""
            });
            selected = lines.getRowCount() - 1;
        }
        final Object selectedRow = lines.getDataVector().get(selected);
        choose("物料", "/api/materials?format=tsv", new String[] {
            "material_id", "name", "unit"
        }, new String[] {
            "物料编码", "物料名称", "单位"
        }, m -> {
            int row = rowIndex(lines, selectedRow);
            if (row < 0) {
                JOptionPane.showMessageDialog(frame, "原采购明细已删除，请重新选择目标明细。", "选择物料",
                        JOptionPane.INFORMATION_MESSAGE);
                return;
            }
            lines.setValueAt(m.get("material_id"), row, 0);
        });
    }

    String[][] lineValues() {
        String[][] a = new String[lines.getRowCount()][4];
        for (int r = 0; r < a.length; r++) for (int c = 0; c < 4; c++) {
            Object v = lines.getValueAt(r, c);
            a[r][c] = v == null ? "" : v.toString().trim();
        }
        return a;
    }

    void updateAmount() {
        try {
            amount.setText("合计：" + total(lineValues()).toPlainString() + " 元");
        } catch (Exception e) {
            amount.setText("合计：请完善数量和单价");
        }
    }

    void submitOrder() {
        if (lineTable.isEditing() && !lineTable.getCellEditor().stopCellEditing()) return;
        try {
            Map<String, String> f = new LinkedHashMap<String, String>();
            f.put("batch_id", required(batch.getText(), "批次"));
            f.put("supplier_id", required(supplier.getText(), "供应商"));
            f.put("warehouse", required(warehouse.getText(), "仓库"));
            f.put("delivery_date", LocalDate.parse(date.getText().trim()).toString());
            f.put("notes", notes.getText());
            f.put("lines", serializeLines(lineValues()));
            String summary = "供应商：" + supplier.getText()
                    + "\n交货日期：" + date.getText()
                    + "\n明细：" + lines.getRowCount()
                    + " 行\n金额：" + total(lineValues()).toPlainString() + " 元\n确认提交采购单？";
            if (JOptionPane.showConfirmDialog(frame, summary, "确认采购单", JOptionPane.OK_CANCEL_OPTION) != JOptionPane.OK_OPTION) return;
            submit.setEnabled(false);
            async("提交采购单", () -> parseTsv(request("POST", "/api/orders", form(f))), r -> {
                submit.setEnabled(true);
                if (r.isEmpty()) throw new IllegalArgumentException("服务未返回订单号");
                String id = r.get(0).get("order_id");
                JOptionPane.showMessageDialog(frame, "采购单提交成功\n订单号：" + id + "\n状态：" + r.get(0).get("status"),
                "采购单成功", JOptionPane.INFORMATION_MESSAGE);
                status.setText("提交成功：" + id + "；录入内容已保留，请回查订单");
                refreshOrders();
            }, () -> submit.setEnabled(true));
        } catch (Exception e) {
            error(e);
        }
    }

    void submitException() {
        try {
            Map<String, String> f = new LinkedHashMap<String, String>();
            f.put("batch_id", required(context.batchId(), "批次"));
            f.put("material_id", required(exceptionMaterial.getText(), "物料编码"));
            f.put("reason", required(reason.getText(), "异常原因"));
            exceptionSubmit.setEnabled(false);
            async("登记异常", () -> request("POST", "/api/exceptions", form(f)), r -> {
                exceptionSubmit.setEnabled(true);
                JOptionPane.showMessageDialog(frame, "异常登记成功\n" + r);
            }, () -> exceptionSubmit.setEnabled(true));
        } catch (Exception e) {
            error(e);
        }
    }

    <T> void async(String action, Callable<T> work, Consumer<T> done) {
        async(action, work, done, () -> {
        });
    }

    <T> void async(String action, Callable<T> work, Consumer<T> done, Runnable cleanup) {
        async(action, work, done, cleanup, () -> true);
    }

    <T> void async(String action, Callable<T> work, Consumer<T> done, Runnable cleanup,
            BooleanSupplier mayPublish) {
        status.setText(action + "…");
        new SwingWorker<T, Void>() {
            protected T doInBackground() throws Exception {
                return work.call();
            }
            protected void done() {
                try {
                    if (!mayPublish.getAsBoolean()) return;
                    done.accept(get());
                } catch (Exception e) {
                    Throwable cause = e.getCause() == null ? e : e.getCause();
                    error(cause);
                } finally {
                    cleanup.run();
                }
            }
        }
        .execute();
    }

    void error(Throwable e) {
        String message = e.getMessage() == null ? e.toString() : e.getMessage();
        status.setText("操作失败：" + message + "；录入内容已保留，可重试");
        JOptionPane.showMessageDialog(frame, message + "\n录入内容已保留，请检查后重试。", "操作失败", JOptionPane.ERROR_MESSAGE);
    }

    String request(String method, String path, String body) throws IOException {
        return requestAt(base, method, path, body);
    }

    public static String requestAt(String base, String method, String path, String body) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(base + path).openConnection();
        c.setConnectTimeout(8000);
        c.setReadTimeout(15000);
        c.setRequestMethod(method);
        try {
            if (body != null) {
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
                byte[] bytes = body.getBytes("UTF-8");
                c.setFixedLengthStreamingMode(bytes.length);
                try (OutputStream out = c.getOutputStream()) {
                    out.write(bytes);
                }
            }
            int code = c.getResponseCode();
            InputStream input = code >= 400 ? c.getErrorStream() : c.getInputStream();
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            if (input != null) try (InputStream in = input) {
                byte[] b = new byte[4096];
                for (int n; (n = in.read(b)) != - 1;) bytes.write(b, 0, n);
            }
            String text = new String(bytes.toByteArray(), "UTF-8");
            if (code >= 400) throw new IOException("HTTP " + code + "：" + text);
            return text;
        } finally {
            c.disconnect();
        }
    }

    static String required(String s, String label) {
        if (s == null || s.trim().isEmpty()) throw new IllegalArgumentException("请填写" + label);
        return s.trim();
    }

    public static List<Map<String, String>> parseTsv(String text) {
        List<Map<String, String>> rows = new ArrayList<Map<String, String>>();
        String[] records = text.replace("\r\n", "\n").split("\n", - 1);
        if (records.length == 0 || records[0].isEmpty()) return rows;
        String[] headers = records[0].split("\t", - 1);
        for (int i = 1; i < records.length; i++) {
            if (records[i].isEmpty()) continue;
            String[] values = records[i].split("\t", - 1);
            if (values.length != headers.length) throw new IllegalArgumentException("服务返回的表格列数不正确，第 " + (i + 1) + " 行");
            Map<String, String> row = new LinkedHashMap<String, String>();
            for (int c = 0; c < headers.length; c++) row.put(headers[c], values[c]);
            rows.add(row);
        }
        return rows;
    }

    public static String serializeLines(String[][] rows) {
        if (rows.length == 0) throw new IllegalArgumentException("请至少添加一条采购明细");
        StringBuilder out = new StringBuilder();
        for (String[] r : rows) {
            if (r.length != 4) throw new IllegalArgumentException("采购明细列数不正确");
            for (String s : r) if (s == null || s.trim().isEmpty()
                    || s.indexOf('\t') >= 0 || s.indexOf('\n') >= 0 || s.indexOf('\r') >= 0)
                throw new IllegalArgumentException("请完整填写明细，不能包含换行或制表符");
            if (!r[1].matches("[0-9]+") || new BigInteger(r[1]).signum() <= 0) throw new IllegalArgumentException("数量必须为正整数");
            price(r[2]);
            if (out.length() > 0) out.append('\n');
            out.append(r[0]).append('\t').append(r[1]).append('\t').append(r[2]).append('\t').append(r[3]);
        }
        return out.toString();
    }

    static BigDecimal price(String s) {
        try {
            BigDecimal p = new BigDecimal(s);
            if (p.signum() <= 0) throw new ArithmeticException();
            return p.setScale(2, RoundingMode.UNNECESSARY);
        } catch (Exception e) {
            throw new IllegalArgumentException("单价必须为正金额，最多两位小数");
        }
    }

    public static BigDecimal total(String[][] rows) {
        BigDecimal sum = new BigDecimal("0.00");
        for (String[] r : rows) {
            if (!r[1].matches("[0-9]+") || new BigInteger(r[1]).signum() <= 0) throw new IllegalArgumentException("数量必须为正整数");
            sum = sum.add(price(r[2]).multiply(new BigDecimal(r[1])));
        }
        return sum.setScale(2);
    }

    public static String form(Map<String, String> values) throws UnsupportedEncodingException {
        StringBuilder s = new StringBuilder();
        for (Map.Entry<String, String> e : values.entrySet()) {
            if (s.length() > 0) s.append('&');
            s.append(URLEncoder.encode(e.getKey(), "UTF-8")).append('=').append(URLEncoder.encode(e.getValue(),
            "UTF-8"));
        }
        return s.toString();
    }

    public static void main(String[] args) {
        String url = "http://127.0.0.1:8765";
        boolean obstacles = false;
        for (int i = 0; i < args.length; i++) {
            if ("--obstacles".equals(args[i])) obstacles = true;
            else if ("--url".equals(args[i]) && i + 1 < args.length) url = args[++i];
            else throw new IllegalArgumentException("用法：SupplyChainPurchase [--obstacles] --url http://127.0.0.1:8765");
        }
        final String endpoint = url;
        final boolean lazy = obstacles;
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {
            }
            new SupplyChainPurchase(endpoint, lazy);
        });
    }
}
