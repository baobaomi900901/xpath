import java.math.BigDecimal;
import java.util.*;
public class PurchaseModelTest {

    public static void main(String[] args) throws Exception {
        List<Map<String, String>> rows = SupplyChainPurchase.parseTsv("id\tname\textra\r\nM001\t中文\t\r\n");
        check(rows.size() == 1 && rows.get(0).get("name").equals("中文") && rows.get(0).get("extra").equals(""),
        "TSV Unicode and trailing empties");
        boolean bad = false;
        try {
            SupplyChainPurchase.parseTsv("a\tb\nonly");
        } catch (IllegalArgumentException e) {
            bad = true;
        }
        check(bad, "Reject malformed TSV");
        String[][] lines = {
            {
                "M001", "120", "10.00", "Q001"
            }, {
                "M003", "100", "5.10", "Q003"
            }
        };
        check(SupplyChainPurchase.total(lines).equals(new BigDecimal("1710.00")), "Exact decimal total");
        check(SupplyChainPurchase.serializeLines(lines).equals("M001\t120\t10.00\tQ001\nM003\t100\t5.10\tQ003"),
        "Contract lines");
        for (String q : new String[] {
            "0", "-1", "1.5", "abc"
        }) {
            bad = false;
            try {
                SupplyChainPurchase.serializeLines(new String[][] {
                    {
                        "M001", q, "1.00", "Q"
                    }
                });
            } catch (IllegalArgumentException e) {
                bad = true;
            }
            check(bad, "Reject quantity " + q);
        }
        bad = false;
        try {
            SupplyChainPurchase.serializeLines(new String[][] {
                {
                    "M001", "1", "1.001", "Q"
                }
            });
        } catch (IllegalArgumentException e) {
            bad = true;
        }
        check(bad, "Reject fractional cents");
        check(SupplyChainPurchase.form(Collections.singletonMap("reason", "缺货 & 延期")).contains("%26"), "Encoded Chinese form");
        bad = false;
        try {
            SupplyChainPurchase.serializeLines(new String[][] {{"M001", "1", "0.00", "Q"}});
        } catch (IllegalArgumentException e) {
            bad = true;
        }
        check(bad, "Reject zero price to match server");
        javax.swing.table.DefaultTableModel model = new javax.swing.table.DefaultTableModel(
                new String[] {"material"}, 0);
        model.addRow(new String[] {"M001"});
        model.addRow(new String[] {"M002"});
        Object selectedRow = model.getDataVector().get(1);
        model.removeRow(0);
        check(SupplyChainPurchase.rowIndex(model, selectedRow) == 0, "Selected row survives index shift");
        model.removeRow(0);
        model.addRow(new String[] {"M002"});
        check(SupplyChainPurchase.rowIndex(model, selectedRow) == -1,
                "Deleted row cannot select equal-looking replacement");
        SupplyChainPurchase.RequestGeneration generation = new SupplyChainPurchase.RequestGeneration();
        long older = generation.begin();
        long newer = generation.begin();
        check(generation.isCurrent(newer), "Newest refresh may publish");
        check(!generation.isCurrent(older), "Older response cannot overwrite newest refresh");
        System.out.println("PASS PurchaseModelTest");
    }

    static void check(boolean ok, String name) {
        if (!ok) throw new AssertionError(name);
    }
}
