package com.xpath.shootingrange.ui;

import javax.accessibility.Accessible;
import javax.accessibility.AccessibleContext;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import javax.swing.WindowConstants;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.GridBagLayout;
import java.awt.Point;

/** Visible overlapping siblings for reproducing Java point-selection regressions. */
public final class OverlapHitPanel extends JPanel {
    private final JLabel clickStatus = new JLabel("Front Button 点击次数：0");
    private int clicks;

    public OverlapHitPanel() {
        this(true);
    }

    private OverlapHitPanel(boolean allowWindow) {
        setLayout(new BorderLayout(0, 12));
        setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));
        setName("overlap-hit-panel");
        add(buildInstructions(), BorderLayout.NORTH);

        JPanel stage = new JPanel(new GridBagLayout());
        stage.add(buildScene());
        add(stage, BorderLayout.CENTER);
        add(buildActions(allowWindow), BorderLayout.SOUTH);
    }

    private JPanel buildInstructions() {
        JPanel instructions = new JPanel(new BorderLayout(0, 8));
        JLabel title = new JLabel("PR #31：可见重叠控件命中");
        title.setFont(title.getFont().deriveFont(Font.BOLD, 16f));
        instructions.add(title, BorderLayout.NORTH);
        instructions.add(new JLabel("<html>"
                + "优先用 Auto 捕获 Front Button 中心，再用 JAB 对照。<br>"
                + "预期：push button / Front Button；异常：panel / Back Content。<br>"
                + "背景容器更深且同样可见；场景父容器故意不提供无障碍坐标命中。<br>"
                + "JAB 原生命中成功时可能正常，冷态独立窗口可用于按坐标捕获。<br>"
                + "普通鼠标点击仍应命中前景按钮，点击后可在下方查看计数。"
                + "</html>"), BorderLayout.CENTER);
        return instructions;
    }

    private JPanel buildScene() {
        JPanel scene = new NoPointPanel();
        scene.setName("overlap-hit-scene");
        scene.getAccessibleContext().setAccessibleName("Overlap Hit Scene");
        scene.setPreferredSize(new Dimension(500, 300));
        scene.setBackground(Color.WHITE);
        scene.setBorder(BorderFactory.createLineBorder(new Color(185, 196, 210)));

        JPanel back = new JPanel(null);
        back.setName("overlap-back-wrapper");
        back.getAccessibleContext().setAccessibleName("Back Wrapper");
        back.setBounds(20, 20, 300, 200);

        JPanel inner = new JPanel(null);
        inner.setName("overlap-back-content");
        inner.getAccessibleContext().setAccessibleName("Back Content");
        inner.setBackground(new Color(225, 235, 248));
        inner.setBorder(BorderFactory.createTitledBorder("Back Content（背景，层级更深）"));
        inner.setBounds(0, 0, 300, 200);
        back.add(inner);
        scene.add(back);

        JButton front = new JButton("Front Button");
        front.setName("overlap-front-button");
        front.setBounds(40, 40, 160, 40);
        front.addActionListener(event -> clickStatus.setText("Front Button 点击次数：" + ++clicks));
        scene.add(front);
        scene.setComponentZOrder(front, 0);
        return scene;
    }

    private JPanel buildActions(boolean allowWindow) {
        JPanel actions = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        clickStatus.setName("overlap-click-status");
        actions.add(clickStatus);
        if (allowWindow) {
            JButton openWindow = new JButton("打开独立复现窗口");
            openWindow.setName("overlap-open-window");
            openWindow.addActionListener(event -> {
                JFrame window = new JFrame("Java 重叠命中复现 - PR #31");
                window.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
                window.setContentPane(new OverlapHitPanel(false));
                window.setMinimumSize(new Dimension(640, 500));
                window.pack();
                window.setLocationRelativeTo(SwingUtilities.getWindowAncestor(this));
                window.setVisible(true);
            });
            actions.add(openWindow);
        }
        return actions;
    }

    /** Keep mouse routing and accessible children intact; omit only accessible point hits. */
    private static final class NoPointPanel extends JPanel {
        NoPointPanel() {
            super(null);
        }

        @Override
        public AccessibleContext getAccessibleContext() {
            if (accessibleContext == null) {
                accessibleContext = new AccessibleNoPointPanel();
            }
            return accessibleContext;
        }

        protected final class AccessibleNoPointPanel extends AccessibleJPanel {
            @Override
            public Accessible getAccessibleAt(Point point) {
                return null;
            }
        }
    }
}
