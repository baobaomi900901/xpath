import com.sun.net.httpserver.*;
import java.net.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
public class PurchaseHttpTest {

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        AtomicInteger calls = new AtomicInteger();
        server.createContext("/api/orders", e -> {
            byte[] body = read(e.getRequestBody());
            String form = new String(body, "UTF-8");
            if (!e.getRequestMethod().equals("POST") || !form.contains("%E4%B8%AD")) {
                e.sendResponseHeaders(400, - 1);
                e.close();
                return;
            }
            int count = calls.incrementAndGet();
            byte[] response = (count == 1 ? "暂时失败，请重试" : "order_id\ttotal\tstatus\nPO001\t10.00\t待审批\n").getBytes("UTF-8");
            e.sendResponseHeaders(count == 1 ? 503 : 201, response.length);
            e.getResponseBody().write(response);
            e.close();
        });
        server.start();
        try {
            String base = "http://127.0.0.1:" + server.getAddress().getPort();
            String body = SupplyChainPurchase.form(Collections.singletonMap("notes", "中文"));
            boolean failed = false;
            try {
                SupplyChainPurchase.requestAt(base, "POST", "/api/orders", body);
            } catch (IOException ex) {
                failed = ex.getMessage().contains("503") && ex.getMessage().contains("暂时失败");
            }
            if (!failed) throw new AssertionError("503 readable UTF-8 failure");
            String result = SupplyChainPurchase.requestAt(base, "POST", "/api/orders", body);
            if (!SupplyChainPurchase.parseTsv(result).get(0).get("order_id").equals("PO001") || calls.get() != 2) throw new AssertionError("Retry same form yields order");
            System.out.println("PASS PurchaseHttpTest");
        } finally {
            server.stop(0);
        }
    }

    static byte[] read(InputStream in) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] b = new byte[512];
        for (int n; (n = in.read(b)) != - 1;) out.write(b, 0, n);
        return out.toByteArray();
    }
}
