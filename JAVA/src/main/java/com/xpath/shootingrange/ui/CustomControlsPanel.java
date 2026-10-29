package com.xpath.shootingrange.ui;

import javax.swing.JPanel;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Rectangle;
import java.awt.RenderingHints;
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.awt.event.InputMethodEvent;
import java.awt.event.InputMethodListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.text.AttributedCharacterIterator;

/** A single canvas: the apparent controls are pixels, never Swing child components. */
public final class CustomControlsPanel extends JPanel {
    private static final int WIDTH = 944;
    private static final int HEIGHT = 600;
    private static final Color INK = new Color(32, 47, 67);
    private static final Color MUTED = new Color(101, 117, 136);
    private static final Color ACCENT = new Color(35, 109, 210);
    private static final Color LINE = new Color(215, 224, 235);
    private static final String[] MODES = {"基础", "进阶", "完整"};
    private static final String[] OPTIONS = {"文字", "图形", "交互"};
    private static final String[] MONTHS = {"一月", "二月", "三月", "四月", "五月"};
    private static final int[] VALUES = {64, 88, 52, 76, 95};
    private static final Rectangle[] FIELDS = {
            new Rectangle(48, 144, 374, 38), new Rectangle(48, 222, 374, 38)
    };
    private static final Rectangle RESET = new Rectangle(778, 518, 116, 38);
    private final StringBuilder[] values = {new StringBuilder(), new StringBuilder()};
    private final boolean[] checked = new boolean[OPTIONS.length];
    private int mode;
    private int selectedBar = -1;
    // Logical keyboard targets: two fields, three radios, three checkboxes, reset.
    private int active;
    private int caret;

    public CustomControlsPanel() {
        setName("custom-controls-canvas");
        setPreferredSize(new Dimension(WIDTH, HEIGHT));
        setBackground(new Color(241, 245, 250));
        setFocusable(true);
        setFocusTraversalKeysEnabled(false);
        enableInputMethods(true);
        addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent event) {
                if (event.getButton() != MouseEvent.BUTTON1) return;
                requestFocusInWindow();
                double scale = scale();
                int x = (int) ((event.getX() - offsetX()) / scale);
                int y = (int) ((event.getY() - offsetY()) / scale);
                for (int i = 0; i < FIELDS.length; i++) {
                    if (FIELDS[i].contains(x, y)) {
                        active = i;
                        caret = values[i].length();
                        repaint();
                        return;
                    }
                }
                for (int i = 0; i < 3; i++) {
                    if (choiceBounds(i, 294).contains(x, y)) {
                        active = 2 + i;
                        mode = i;
                    }
                    if (choiceBounds(i, 362).contains(x, y)) {
                        active = 5 + i;
                        checked[i] = !checked[i];
                    }
                }
                for (int i = 0; i < VALUES.length; i++) {
                    if (barBounds(i).contains(x, y)) selectedBar = i;
                }
                if (RESET.contains(x, y)) reset();
                repaint();
            }
        });
        addKeyListener(new KeyAdapter() {
            @Override
            public void keyTyped(KeyEvent event) {
                char ch = event.getKeyChar();
                if (active < 2 && !event.isControlDown() && !event.isAltDown()
                        && !Character.isISOControl(ch)) insert(String.valueOf(ch));
            }

            @Override
            public void keyPressed(KeyEvent event) {
                handleKey(event);
            }
        });
        // Passive input-method client: the OS composition window handles pre-edit text.
        addInputMethodListener(new InputMethodListener() {
            @Override
            public void inputMethodTextChanged(InputMethodEvent event) {
                AttributedCharacterIterator text = event.getText();
                if (text != null && active < 2) {
                    StringBuilder committed = new StringBuilder();
                    char ch = text.first();
                    for (int i = 0; i < event.getCommittedCharacterCount(); i++) {
                        if (!Character.isISOControl(ch)) committed.append(ch);
                        ch = text.next();
                    }
                    insert(committed.toString());
                }
                event.consume();
            }

            @Override
            public void caretPositionChanged(InputMethodEvent event) {
                event.consume();
            }
        });
        addFocusListener(new FocusAdapter() {
            @Override
            public void focusGained(FocusEvent event) { repaint(); }

            @Override
            public void focusLost(FocusEvent event) { repaint(); }
        });
    }

    private void insert(String text) {
        if (active >= 2 || text.isEmpty()) return;
        StringBuilder value = values[active];
        // Keep this small test field bounded, including IME commits.
        if (value.length() + text.length() <= 80) {
            value.insert(caret, text);
            caret += text.length();
            repaint();
        }
    }

    private void handleKey(KeyEvent event) {
        int key = event.getKeyCode();
        if (key == KeyEvent.VK_TAB) {
            int next = active + (event.isShiftDown() ? -1 : 1);
            if (next < 0) transferFocusBackward();
            else if (next > 8) transferFocus();
            else {
                active = next;
                if (active < 2) caret = values[active].length();
            }
            event.consume();
        } else if (active < 2) {
            StringBuilder value = values[active];
            if (key == KeyEvent.VK_BACK_SPACE && caret > 0) {
                int previous = value.offsetByCodePoints(caret, -1);
                value.delete(previous, caret);
                caret = previous;
            } else if (key == KeyEvent.VK_DELETE && caret < value.length()) {
                value.delete(caret, value.offsetByCodePoints(caret, 1));
            } else if (key == KeyEvent.VK_LEFT && caret > 0) {
                caret = value.offsetByCodePoints(caret, -1);
            } else if (key == KeyEvent.VK_RIGHT && caret < value.length()) {
                caret = value.offsetByCodePoints(caret, 1);
            } else if (key == KeyEvent.VK_HOME) caret = 0;
            else if (key == KeyEvent.VK_END) caret = value.length();
        } else if (key == KeyEvent.VK_SPACE || key == KeyEvent.VK_ENTER) {
            if (active < 5) mode = active - 2;
            else if (active < 8) checked[active - 5] = !checked[active - 5];
            else {
                reset();
                // Keep keyboard focus on the button through the following KEY_TYPED event.
                active = 8;
            }
            event.consume();
        }
        repaint();
    }

    private void reset() {
        for (StringBuilder value : values) value.setLength(0);
        for (int i = 0; i < checked.length; i++) checked[i] = false;
        mode = 0;
        selectedBar = -1;
        active = 0;
        caret = 0;
    }

    private double scale() {
        return Math.max(0.01, Math.min(getWidth() / (double) WIDTH, getHeight() / (double) HEIGHT));
    }

    private double offsetX() { return (getWidth() - WIDTH * scale()) / 2; }
    private double offsetY() { return (getHeight() - HEIGHT * scale()) / 2; }

    private static Rectangle choiceBounds(int index, int y) {
        return new Rectangle(48 + index * 126, y, 116, 30);
    }

    private static Rectangle barBounds(int index) {
        int height = VALUES[index] * 2;
        return new Rectangle(548 + index * 68, 354 - height, 42, height);
    }

    @Override
    protected void paintComponent(Graphics graphics) {
        super.paintComponent(graphics);
        Graphics2D g = (Graphics2D) graphics.create();
        try {
            g.translate(offsetX(), offsetY());
            g.scale(scale(), scale());
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
            text(g, "自绘控件", 26, 35, 24, INK, true);
            text(g, "画布探测样本 · 输入、选择和图表均由 Graphics2D 绘制", 26, 62, 13, MUTED, false);
            card(g, 26, 86, 418, 328);
            card(g, 464, 86, 454, 328);
            card(g, 26, 432, 892, 142);
            drawForm(g);
            drawChart(g);
            drawTextPanel(g);
            text(g, "操作：点击输入框输入文字；Tab 切换，空格选择；点击柱形查看数值。", 26, 593, 12, MUTED, false);
        } finally {
            g.dispose();
        }
    }

    private void drawForm(Graphics2D g) {
        text(g, "画布表单", 48, 113, 16, INK, true);
        String[] labels = {"姓名", "备注"};
        String[] hints = {"请输入姓名", "请输入测试内容（最多 80 字符）"};
        for (int i = 0; i < FIELDS.length; i++) {
            Rectangle r = FIELDS[i];
            text(g, labels[i], r.x, r.y - 8, 12, MUTED, false);
            g.setColor(new Color(249, 251, 254));
            g.fillRoundRect(r.x, r.y, r.width, r.height, 10, 10);
            g.setColor(hasFocus() && active == i ? ACCENT : LINE);
            g.drawRoundRect(r.x, r.y, r.width, r.height, 10, 10);
            Graphics2D field = (Graphics2D) g.create();
            try {
                field.clipRect(r.x + 10, r.y + 2, r.width - 20, r.height - 4);
                field.setFont(new Font("Dialog", Font.PLAIN, 14));
                String value = values[i].toString();
                int caretWidth = field.getFontMetrics().stringWidth(value.substring(0, active == i ? caret : value.length()));
                int shift = Math.max(0, caretWidth - (r.width - 24));
                field.setColor(value.isEmpty() ? MUTED : INK);
                field.drawString(value.isEmpty() ? hints[i] : value, r.x + 11 - shift, r.y + 25);
                if (hasFocus() && active == i) {
                    field.setColor(ACCENT);
                    int cx = r.x + 11 + caretWidth - shift;
                    field.drawLine(cx, r.y + 9, cx, r.y + 29);
                }
            } finally {
                field.dispose();
            }
        }
        text(g, "测试模式 · 单选", 48, 286, 12, MUTED, false);
        text(g, "探测内容 · 多选", 48, 354, 12, MUTED, false);
        for (int i = 0; i < 3; i++) {
            Rectangle radio = choiceBounds(i, 294);
            focusOutline(g, radio, active == 2 + i);
            g.setColor(mode == i ? ACCENT : MUTED);
            g.drawOval(radio.x + 4, radio.y + 7, 16, 16);
            if (mode == i) g.fillOval(radio.x + 8, radio.y + 11, 8, 8);
            text(g, MODES[i], radio.x + 30, radio.y + 21, 14, INK, false);
            Rectangle box = choiceBounds(i, 362);
            focusOutline(g, box, active == 5 + i);
            g.setColor(checked[i] ? ACCENT : MUTED);
            g.drawRoundRect(box.x + 4, box.y + 7, 16, 16, 4, 4);
            if (checked[i]) {
                g.fillRoundRect(box.x + 4, box.y + 7, 16, 16, 4, 4);
                g.setColor(Color.WHITE);
                g.setStroke(new BasicStroke(2));
                g.drawLine(box.x + 7, box.y + 15, box.x + 11, box.y + 19);
                g.drawLine(box.x + 11, box.y + 19, box.x + 17, box.y + 11);
                g.setStroke(new BasicStroke(1));
            }
            text(g, OPTIONS[i], box.x + 30, box.y + 21, 14, INK, false);
        }
    }

    private void drawChart(Graphics2D g) {
        text(g, "月度样本数量", 486, 113, 16, INK, true);
        text(g, "单位：个 · 点击柱形选择", 486, 136, 12, MUTED, false);
        for (int value = 0; value <= 100; value += 25) {
            int y = 354 - value * 2;
            g.setColor(LINE);
            g.drawLine(536, y, 894, y);
            text(g, String.valueOf(value), 500, y + 4, 11, MUTED, false);
        }
        for (int i = 0; i < VALUES.length; i++) {
            Rectangle bar = barBounds(i);
            g.setColor(selectedBar == i ? new Color(20, 151, 129) : ACCENT);
            g.fillRoundRect(bar.x, bar.y, bar.width, bar.height, 6, 6);
            text(g, String.valueOf(VALUES[i]), bar.x + 12, bar.y - 8, 12, INK, true);
            text(g, MONTHS[i], bar.x + 7, 378, 12, MUTED, false);
        }
        text(g, "固定测试数据，便于重复定位和比较", 536, 400, 12, MUTED, false);
    }

    private void drawTextPanel(Graphics2D g) {
        text(g, "文字面板 / 当前状态", 48, 460, 16, INK, true);
        text(g, "这段文字、边框和下面的状态均绘制在同一块画布上。", 48, 485, 13, MUTED, false);
        Graphics2D summary = (Graphics2D) g.create();
        try {
            summary.clipRect(48, 492, 710, 70);
            text(summary, "姓名：" + displayValue(0) + "    备注：" + displayValue(1), 48, 510, 13, INK, false);
            StringBuilder selection = new StringBuilder();
            for (int i = 0; i < checked.length; i++) {
                if (checked[i]) selection.append(OPTIONS[i]).append(" ");
            }
            text(summary, "模式：" + MODES[mode] + "    多选：" + (selection.length() == 0 ? "未选择" : selection),
                    48, 533, 13, INK, false);
            String chart = selectedBar < 0 ? "未选择柱形" : MONTHS[selectedBar] + " / " + VALUES[selectedBar] + " 个";
            text(summary, "图表：" + chart, 48, 555, 13, INK, false);
        } finally {
            summary.dispose();
        }
        g.setColor(ACCENT);
        g.fillRoundRect(RESET.x, RESET.y, RESET.width, RESET.height, 10, 10);
        text(g, "重置样本", RESET.x + 26, RESET.y + 25, 14, Color.WHITE, true);
        focusOutline(g, new Rectangle(RESET.x - 3, RESET.y - 3, RESET.width + 6, RESET.height + 6), active == 8);
    }

    private String displayValue(int index) {
        String value = values[index].toString();
        if (value.isEmpty()) return "（空）";
        int count = value.codePointCount(0, value.length());
        return count > 18 ? value.substring(0, value.offsetByCodePoints(0, 18)) + "…" : value;
    }

    private void focusOutline(Graphics2D g, Rectangle rectangle, boolean selected) {
        if (hasFocus() && selected) {
            g.setColor(ACCENT);
            g.drawRoundRect(rectangle.x, rectangle.y, rectangle.width, rectangle.height, 6, 6);
        }
    }

    private static void card(Graphics2D g, int x, int y, int width, int height) {
        g.setColor(Color.WHITE);
        g.fillRoundRect(x, y, width, height, 16, 16);
        g.setColor(LINE);
        g.drawRoundRect(x, y, width, height, 16, 16);
    }

    private static void text(Graphics2D g, String value, int x, int y, int size, Color color, boolean bold) {
        g.setFont(new Font("Dialog", bold ? Font.BOLD : Font.PLAIN, size));
        g.setColor(color);
        g.drawString(value, x, y);
    }
}
