package com.xpath.shootingrange.ui;

import javax.swing.*;
import java.awt.*;

/** Layout shared by the two standard-control sample pages. */
final class SamplePanelLayout {
    private SamplePanelLayout() { }

    static <T extends JComponent> T named(T component, String name) {
        component.setName(name);
        component.getAccessibleContext().setAccessibleName(name);
        return component;
    }

    static JPanel card(String title, JComponent... rows) {
        JPanel content = new JPanel(new GridBagLayout());
        content.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createTitledBorder(title), BorderFactory.createEmptyBorder(8, 10, 10, 10)));
        GridBagConstraints c = new GridBagConstraints();
        c.gridx = 0; c.weightx = 1; c.fill = GridBagConstraints.HORIZONTAL;
        c.insets = new Insets(3, 0, 5, 0);
        for (JComponent row : rows) {
            c.gridy++;
            content.add(row, c);
        }
        c.gridy++; c.weighty = 1;
        content.add(Box.createVerticalGlue(), c);
        return content;
    }

    static JPanel row(JComponent... components) {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        for (JComponent component : components) panel.add(component);
        return panel;
    }

    static JPanel field(String label, JComponent component) {
        JPanel panel = new JPanel(new BorderLayout(8, 0));
        JLabel caption = new JLabel(label);
        caption.setPreferredSize(new Dimension(Math.max(100, caption.getPreferredSize().width), caption.getPreferredSize().height));
        caption.setLabelFor(component);
        panel.add(caption, BorderLayout.WEST);
        panel.add(component, BorderLayout.CENTER);
        return panel;
    }

    static JScrollPane page(JComponent cards, JComponent footer) {
        JPanel content = new ResponsiveContent();
        content.setLayout(new BorderLayout(12, 12));
        content.setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));
        content.add(cards, BorderLayout.CENTER);
        content.add(footer, BorderLayout.SOUTH);
        JScrollPane scroll = new JScrollPane(content);
        scroll.setBorder(BorderFactory.createEmptyBorder());
        scroll.getVerticalScrollBar().setUnitIncrement(24);
        return scroll;
    }

    private static final class ResponsiveContent extends JPanel implements Scrollable {
        public Dimension getPreferredScrollableViewportSize() { return getPreferredSize(); }
        public int getScrollableUnitIncrement(Rectangle r, int orientation, int direction) { return 24; }
        public int getScrollableBlockIncrement(Rectangle r, int orientation, int direction) { return Math.max(24, r.height - 24); }
        public boolean getScrollableTracksViewportWidth() { return true; }
        public boolean getScrollableTracksViewportHeight() {
            return getParent() instanceof JViewport && getPreferredSize().height < getParent().getHeight();
        }
    }
}
