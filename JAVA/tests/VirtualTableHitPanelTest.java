import com.xpath.shootingrange.ui.VirtualTableHitPanel;
import javax.accessibility.AccessibleContext;
import javax.accessibility.AccessibleRole;
import javax.accessibility.AccessibleTable;
import javax.imageio.ImageIO;
import javax.swing.JButton;
import javax.swing.JPanel;
import javax.swing.JTable;
import javax.swing.SwingUtilities;
import java.awt.Component;
import java.awt.Container;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import java.io.File;

/** Checks real renderer roles and the repeated-text / checkbox reproduction model. */
public final class VirtualTableHitPanelTest {
    public static void main(String[] args) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            try {
                JPanel panel = new VirtualTableHitPanel();
                panel.setSize(944, 600);
                layout(panel);
                JTable table = (JTable) find(panel, "virtual-table-employees");
                check(table != null && table.getRowCount() == 2 && table.getColumnCount() == 3,
                        "Reproduction must contain six cells");
                check("Employees".equals(table.getAccessibleContext().getAccessibleName()),
                        "The incorrectly captured table must have a stable name");
                check("Employee columns".equals(table.getTableHeader().getAccessibleContext().getAccessibleName()),
                        "Header must remain identifiable");
                AccessibleTable accessible = table.getAccessibleContext().getAccessibleTable();
                for (int row = 0; row < 2; row++) {
                    for (int column = 0; column < 3; column++) {
                        AccessibleContext cell = accessible.getAccessibleAt(row, column).getAccessibleContext();
                        check(cell.getAccessibleRole() == (column == 1 ? AccessibleRole.CHECK_BOX : AccessibleRole.LABEL),
                                "Cells must expose their standard renderer role");
                        if (column != 1) check("same".equals(cell.getAccessibleName()), "Text cells must keep duplicate names");
                        Rectangle rect = table.getCellRect(row, column, true);
                        Point center = new Point(rect.x + rect.width / 2, rect.y + rect.height / 2);
                        check(rect.width > 0 && rect.height == 30, "Cell geometry must remain usable");
                        check(table.rowAtPoint(center) == row && table.columnAtPoint(center) == column,
                                "The cell center must map back to its row and column");
                    }
                }
                table.setValueAt("edited", 0, 0);
                table.setValueAt(Boolean.FALSE, 0, 1);
                ((JButton) find(panel, "virtual-table-reset")).doClick(0);
                check("same".equals(table.getValueAt(0, 0)) && Boolean.TRUE.equals(table.getValueAt(0, 1)),
                        "Reset must restore the original mixed data");
                check(Boolean.FALSE.equals(table.getValueAt(1, 1)), "Rows must retain different checkbox values");
                layout(panel);
                if (args.length > 0) {
                    BufferedImage image = new BufferedImage(944, 600, BufferedImage.TYPE_INT_RGB);
                    Graphics2D graphics = image.createGraphics();
                    panel.printAll(graphics);
                    graphics.dispose();
                    ImageIO.write(image, "png", new File(args[0]));
                }
                System.out.println("Virtual table geometry, renderer roles, duplicate names and reset passed.");
            } catch (Exception failure) {
                throw new RuntimeException(failure);
            }
        });
    }

    private static Component find(Component component, String name) {
        if (name.equals(component.getName())) return component;
        if (component instanceof Container) {
            for (Component child : ((Container) component).getComponents()) {
                Component found = find(child, name);
                if (found != null) return found;
            }
        }
        return null;
    }

    private static void layout(Container parent) {
        parent.doLayout();
        for (Component child : parent.getComponents()) {
            if (child instanceof Container) layout((Container) child);
        }
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
