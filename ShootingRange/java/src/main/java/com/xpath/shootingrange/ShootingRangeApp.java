package com.xpath.shootingrange;

import com.xpath.shootingrange.ui.AboutPanel;
import com.xpath.shootingrange.ui.FormPanel;
import com.xpath.shootingrange.ui.TablePanel;

import javax.swing.JFrame;
import javax.swing.JTabbedPane;
import javax.swing.WindowConstants;
import java.awt.Dimension;

public class ShootingRangeApp extends JFrame {
    public ShootingRangeApp() {
        super("Java 靶场 - JDK " + System.getProperty("java.version"));
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(960, 680));
        setLocationRelativeTo(null);

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab("表单控件", new FormPanel());
        tabs.addTab("表格数据", new TablePanel());
        tabs.addTab("关于", new AboutPanel());

        setContentPane(tabs);
        pack();
        setSize(1024, 720);
    }
}
