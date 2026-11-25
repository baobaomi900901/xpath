import javax.swing.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class PurchaseLazyTest {
    public static void main(String[] args) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            AtomicInteger count = new AtomicInteger();
            SupplyChainPurchase.LazyPage page = new SupplyChainPurchase.LazyPage("采购", () -> { count.incrementAndGet(); return new JPanel(); });
            if (count.get() != 0) throw new AssertionError("factory ran before request");
            page.request(); page.request();
            if (!page.timer.isRunning() || page.timer.getInitialDelay() != 1200 || count.get() != 0) throw new AssertionError("request must defer once");
            page.finish();
            JComponent built = page.content;
            page.request(); page.finish();
            if (count.get() != 1 || page.content != built) throw new AssertionError("page must be reused");
            SupplyChainPurchase.LazyPage cancelled = new SupplyChainPurchase.LazyPage("异常", () -> { count.incrementAndGet(); return new JPanel(); });
            cancelled.request(); cancelled.close(); cancelled.finish(); cancelled.request();
            if (cancelled.timer.isRunning() || count.get() != 1) throw new AssertionError("closed page constructed");
            Map<String,String> values = new HashMap<String,String>();
            values.put("batch_id", "B1"); values.put("warehouse", "W1"); values.put("deadline", "2026-11-30");
            SupplyChainPurchase.TaskContext early = new SupplyChainPurchase.TaskContext();
            early.accept(values);
            JTextField b = new JTextField(), w = new JTextField(), d = new JTextField();
            early.bind(b,w,d);
            if (!"B1".equals(b.getText()) || !"W1".equals(w.getText()) || !"2026-11-30".equals(d.getText())) throw new AssertionError("early context lost");
            SupplyChainPurchase.TaskContext late = new SupplyChainPurchase.TaskContext();
            late.bind(b,w,d); values.put("batch_id", "B2"); late.accept(values);
            if (!"B2".equals(b.getText()) || !"B2".equals(late.batchId())) throw new AssertionError("late context lost");
            SupplyChainPurchase.TaskContext exceptionOnly = new SupplyChainPurchase.TaskContext(); exceptionOnly.accept(values);
            if (!"B2".equals(exceptionOnly.batchId())) throw new AssertionError("exception requires procurement UI");
        });
        java.util.concurrent.CountDownLatch fired = new java.util.concurrent.CountDownLatch(1);
        long started = System.nanoTime();
        SwingUtilities.invokeAndWait(() -> {
            SupplyChainPurchase.LazyPage page = new SupplyChainPurchase.LazyPage("订单", () -> {
                if (!SwingUtilities.isEventDispatchThread()) throw new AssertionError("factory off EDT");
                fired.countDown(); return new JPanel();
            });
            page.request();
        });
        if (!fired.await(5, java.util.concurrent.TimeUnit.SECONDS)) throw new AssertionError("timer did not build page");
        if ((System.nanoTime() - started) / 1000000 < 1100) throw new AssertionError("page built before load delay");
        System.out.println("PurchaseLazyTest passed");
    }
}
