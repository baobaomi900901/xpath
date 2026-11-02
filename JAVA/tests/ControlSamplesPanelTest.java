import com.xpath.shootingrange.ui.ControlSamplesPanel;
import com.xpath.shootingrange.ui.DynamicSamplesPanel;
import javax.swing.*;
import javax.swing.tree.DefaultMutableTreeNode;
import java.awt.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Headless tests of the real Swing controls, including their accessible selection. */
public final class ControlSamplesPanelTest {
    static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static List<Component> all(Component parent) {
        List<Component> result = new ArrayList<Component>();
        result.add(parent);
        if (parent instanceof Container) for (Component child : ((Container) parent).getComponents()) result.addAll(all(child));
        return result;
    }
    static <T extends Component> T find(Component parent, String name, Class<T> type) {
        for (Component component : all(parent)) {
            if (type.isInstance(component) && (name.equals(component.getName()) ||
                    component instanceof AbstractButton && name.equals(((AbstractButton) component).getText()))) return type.cast(component);
        }
        throw new AssertionError("Missing control: " + name);
    }
    static void click(Component parent, String text) { find(parent, text, AbstractButton.class).doClick(); }
    static void layout(Container parent) {
        parent.doLayout();
        for (Component child : parent.getComponents()) if (child instanceof Container) layout((Container) child);
    }
    static void selection() {
        ControlSamplesPanel page = new ControlSamplesPanel();
        JList<?> single = find(page, "示例单选列表", JList.class);
        JList<?> multiple = find(page, "示例多选列表", JList.class);
        JList<?> empty = find(page, "示例空列表", JList.class);
        check(single.getSelectionMode() == ListSelectionModel.SINGLE_SELECTION, "Single list must remain single");
        check(multiple.getSelectionMode() == ListSelectionModel.MULTIPLE_INTERVAL_SELECTION, "Multiple list mode");
        check(Arrays.equals(multiple.getSelectedIndices(), new int[]{0, 1}), "Initial multiple selection");
        check(empty.getModel().getSize() == 0, "Empty list must contain no placeholder option");
        check(multiple.getModel().getElementAt(3).equals(multiple.getModel().getElementAt(4)), "Two real duplicate items");
        javax.accessibility.AccessibleSelection selection = multiple.getAccessibleContext().getAccessibleSelection();
        selection.clearAccessibleSelection(); selection.addAccessibleSelection(3); selection.addAccessibleSelection(4);
        check(selection.getAccessibleSelectionCount() == 2, "Accessible selection must retain both duplicate items");
        JTextField readonly = find(page, "只读文本", JTextField.class);
        JTextField disabled = find(page, "禁用文本", JTextField.class);
        JTextField hidden = find(page, "显隐文本", JTextField.class);
        check(!readonly.isEditable() && !disabled.isEnabled(), "Text state defaults");
        click(page, "切换禁用状态"); check(disabled.isEnabled(), "Enable control");
        click(page, "显示 / 隐藏输入"); check(!hidden.isVisible(), "Hide control");
        JSlider slider = find(page, "示例滑块", JSlider.class);
        slider.setValue(73);
        check(find(page, "示例进度", JProgressBar.class).getValue() == 73, "Progress must follow slider");
        click(page, "执行一次");
        check(all(page).stream().anyMatch(c -> c instanceof JLabel && "已执行：1 次".equals(((JLabel) c).getText())), "Action counter");
        String text = find(page, "长文本内容", JTextArea.class).getText();
        check(text.length() > 12000 && text.contains("第 360 行") && text.contains("🙂"), "Long Unicode sample");
        for (Dimension size : new Dimension[]{new Dimension(916, 560), new Dimension(980, 620), new Dimension(1240, 720)}) {
            page.setSize(size); layout(page);
            JScrollPane scroll = (JScrollPane) SwingUtilities.getAncestorOfClass(JScrollPane.class, multiple);
            check(scroll.getViewport().getHeight() >= 5 * multiple.getFontMetrics(multiple.getFont()).getHeight(), "List viewport must not collapse");
        }
        click(page, "重置选择与状态");
        check(Arrays.equals(multiple.getSelectedIndices(), new int[]{0, 1}) && single.getSelectedIndex() == 0, "Selection reset");
        check(!disabled.isEnabled() && hidden.isVisible() && slider.getValue() == 35, "State reset");
    }
    static void dynamic() {
        DynamicSamplesPanel page = new DynamicSamplesPanel();
        JTextField old = find(page, "动态输入", JTextField.class);
        click(page, "替换输入对象");
        JTextField fresh = find(page, "动态输入", JTextField.class);
        check(old != fresh && old.getParent() == null && old.getText().equals(fresh.getText()), "Replace object without changing its value/name");
        JPanel group = find(page, "动态选项组", JPanel.class);
        JPanel neighbor = find(page, "相邻选项组", JPanel.class);
        JCheckBox first = (JCheckBox) group.getComponent(0); first.setSelected(true);
        click(page, "替换首项");
        check(first != group.getComponent(0) && ((JCheckBox) group.getComponent(0)).isSelected(), "Replace choice and retain its state");
        for (int i = 0; i < 20; i++) click(page, "增加同名项");
        check(group.getComponentCount() == 23 && neighbor.getComponentCount() == 1, "Dynamic group must not absorb adjacent controls");
        for (int i = 0; i < 24; i++) click(page, "移除首项");
        check(group.getComponentCount() == 0, "Remove including empty group");
        click(page, "替换首项");
        JTable table = find(page, "混合数据表格", JTable.class);
        Object model = table.getModel(); click(page, "替换表格模型");
        check(model != table.getModel() && table.getRowCount() == 3 && table.getColumnCount() == 3, "Replace typed table model");
        check(table.getColumnClass(2) == Boolean.class && table.isCellEditable(0, 2) && !table.isCellEditable(0, 0), "Mixed cell types");
        click(page, "切换排序"); check(table.getValueAt(0, 0).equals(1), "Sort numeric IDs");
        JTree tree = find(page, "示例树", JTree.class);
        click(page, "添加树节点");
        check(((DefaultMutableTreeNode) tree.getModel().getRoot()).getChildCount() == 3, "Add tree member");
        click(page, "重置动态样本");
        check(group.getComponentCount() == 3 && ((DefaultMutableTreeNode) tree.getModel().getRoot()).getChildCount() == 2, "Reset sample structure");
        check(table.getValueAt(0, 0).equals(3), "Reset sorting");
    }
    public static void main(String[] args) throws Exception {
        SwingUtilities.invokeAndWait(() -> { selection(); dynamic(); });
        System.out.println("Control sample checks passed.");
    }
}
