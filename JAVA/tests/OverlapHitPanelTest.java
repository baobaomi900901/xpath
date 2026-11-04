import com.xpath.shootingrange.ui.OverlapHitPanel;
import javax.accessibility.AccessibleContext;
import javax.accessibility.AccessibleRole;
import javax.imageio.ImageIO;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import java.awt.Component;
import java.awt.Container;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.image.BufferedImage;
import java.io.File;

/** Checks the reproduction contract without starting the automation provider. */
public final class OverlapHitPanelTest {
    public static void main(String[] args) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            try {
                JPanel panel = new OverlapHitPanel();
                panel.setSize(944, 600);
                layout(panel);
                JPanel scene = (JPanel) find(panel, "overlap-hit-scene");
                JButton front = (JButton) find(panel, "overlap-front-button");
                JPanel back = (JPanel) find(panel, "overlap-back-content");
                Point center = SwingUtilities.convertPoint(front,
                        front.getWidth() / 2, front.getHeight() / 2, scene);
                check(SwingUtilities.getDeepestComponentAt(scene, center.x, center.y) == front,
                        "Ordinary mouse hit must resolve to the front button");
                Point backgroundPoint = SwingUtilities.convertPoint(scene, center, back);
                check(back.contains(backgroundPoint), "Background must cover the same point");
                check(depth(back, scene) > depth(front, scene), "Background must be deeper");
                check(front.getAccessibleContext().getAccessibleRole() == AccessibleRole.PUSH_BUTTON,
                        "Expected target must expose a real button");
                check(back.getAccessibleContext().getAccessibleRole() == AccessibleRole.PANEL,
                        "Wrong target must remain a panel");
                AccessibleContext context = scene.getAccessibleContext();
                check(context.getAccessibleChildrenCount() == 2,
                        "Accessible children must remain available for fallback traversal");
                check(context.getAccessibleComponent().getAccessibleAt(center) == null,
                        "The scene must deliberately omit accessible point hits");
                front.doClick(0);
                front.doClick(0);
                check(((JLabel) find(panel, "overlap-click-status")).getText().endsWith("2"),
                        "Front button actions must update the visible click count");
                if (args.length > 0) {
                    BufferedImage image = new BufferedImage(944, 600, BufferedImage.TYPE_INT_RGB);
                    Graphics2D graphics = image.createGraphics();
                    panel.printAll(graphics);
                    graphics.dispose();
                    ImageIO.write(image, "png", new File(args[0]));
                }
                System.out.println("Overlap geometry, mouse routing, accessible fallback and button action passed.");
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

    private static int depth(Component component, Component root) {
        if (component == root) return 0;
        check(component.getParent() != null, "Target must belong to the scene");
        return 1 + depth(component.getParent(), root);
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
