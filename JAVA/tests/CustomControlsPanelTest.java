import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import java.awt.Graphics2D;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.event.MouseEvent;
import java.awt.event.InputMethodEvent;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Arrays;
import java.text.AttributedString;
import javax.imageio.ImageIO;

/** Standalone, headless interaction/structure checks; no test dependencies required. */
public final class CustomControlsPanelTest {
    public static void main(String[] args) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            try {
                Class<?> type;
                try {
                    type = Class.forName("com.xpath.shootingrange.ui.CustomControlsPanel");
                } catch (ClassNotFoundException missing) {
                    throw new AssertionError("The custom-controls canvas is missing", missing);
                }
                JPanel panel = (JPanel) type.getDeclaredConstructor().newInstance();
                panel.setSize(944, 600);
                check(panel.getComponentCount() == 0, "Canvas must not contain standard child controls");
                check(panel.getAccessibleContext().getAccessibleChildrenCount() == 0,
                        "Painted elements must not be exposed as accessible child controls");
                int[] initial = pixels(panel);
                click(panel, 180, 163);
                type(panel, 'A');
                int[] typed = pixels(panel);
                check(!Arrays.equals(initial, typed), "Typing must change the rendered field");
                press(panel, KeyEvent.VK_BACK_SPACE);
                check(Arrays.equals(initial, pixels(panel)), "Backspace must remove typed text");
                click(panel, 210, 309);
                int[] radio = pixels(panel);
                check(!Arrays.equals(initial, radio), "Radio selection must update rendering");
                click(panel, 210, 309);
                check(Arrays.equals(radio, pixels(panel)), "Selected radio must remain selected");
                click(panel, 65, 377);
                check(!Arrays.equals(radio, pixels(panel)), "Checkbox must toggle on");
                click(panel, 65, 377);
                check(Arrays.equals(radio, pixels(panel)), "Checkbox must toggle off");
                click(panel, 580, 285);
                check(!Arrays.equals(radio, pixels(panel)), "Clicking a bar must update the text panel");
                click(panel, 180, 163);
                type(panel, '测');
                type(panel, '试');
                ImageIO.write(render(panel), "png", new File("JAVA/target/custom-controls-preview.png"));
                click(panel, 839, 537);
                check(Arrays.equals(initial, pixels(panel)), "Reset must restore all initial values");
                type(panel, '测');
                type(panel, '试');
                int[] chinese = pixels(panel);
                click(panel, 839, 537);
                panel.dispatchEvent(new InputMethodEvent(panel, InputMethodEvent.INPUT_METHOD_TEXT_CHANGED,
                        new AttributedString("测试").getIterator(), 2, null, null));
                check(Arrays.equals(chinese, pixels(panel)), "IME commits must update the custom input");
                press(panel, KeyEvent.VK_HOME);
                press(panel, KeyEvent.VK_DELETE);
                press(panel, KeyEvent.VK_END);
                press(panel, KeyEvent.VK_BACK_SPACE);
                check(Arrays.equals(initial, pixels(panel)), "Caret navigation and delete must edit the input");
                press(panel, KeyEvent.VK_TAB);
                type(panel, 'B');
                check(!Arrays.equals(initial, pixels(panel)), "Tab must reach the second input");
                press(panel, KeyEvent.VK_BACK_SPACE);
                check(Arrays.equals(initial, pixels(panel)), "Second input must be editable");
                press(panel, KeyEvent.VK_TAB);
                press(panel, KeyEvent.VK_TAB);
                press(panel, KeyEvent.VK_SPACE);
                check(Arrays.equals(radio, pixels(panel)), "Keyboard must select the same radio as mouse");
                for (int i = 0; i < 5; i++) press(panel, KeyEvent.VK_TAB);
                press(panel, KeyEvent.VK_SPACE);
                type(panel, ' ');
                check(Arrays.equals(initial, pixels(panel)), "Space on reset must not type into an input");
                panel.setSize(1180, 750);
                int[] resized = pixels(panel);
                click(panel, 263, 386);
                check(!Arrays.equals(resized, pixels(panel)), "Hit testing must follow canvas scaling");
                System.out.println("Custom canvas structure, input, selection, chart, reset and scaling passed.");
            } catch (Exception failure) {
                throw new RuntimeException(failure);
            }
        });
    }

    private static void click(JPanel panel, int x, int y) {
        panel.dispatchEvent(new MouseEvent(panel, MouseEvent.MOUSE_PRESSED,
                System.currentTimeMillis(), 0, x, y, 1, false, MouseEvent.BUTTON1));
    }

    private static void type(JPanel panel, char value) {
        KeyEvent event = new KeyEvent(panel, KeyEvent.KEY_TYPED, System.currentTimeMillis(),
                0, KeyEvent.VK_UNDEFINED, value);
        for (KeyListener listener : panel.getKeyListeners()) listener.keyTyped(event);
    }

    private static void press(JPanel panel, int code) {
        KeyEvent event = new KeyEvent(panel, KeyEvent.KEY_PRESSED, System.currentTimeMillis(),
                0, code, KeyEvent.CHAR_UNDEFINED);
        for (KeyListener listener : panel.getKeyListeners()) listener.keyPressed(event);
    }

    private static BufferedImage render(JPanel panel) {
        BufferedImage image = new BufferedImage(panel.getWidth(), panel.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        panel.paint(graphics);
        graphics.dispose();
        return image;
    }

    private static int[] pixels(JPanel panel) {
        BufferedImage image = render(panel);
        return image.getRGB(0, 0, image.getWidth(), image.getHeight(), null, 0, image.getWidth());
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
