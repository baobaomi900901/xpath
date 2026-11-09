using System;
using System.Collections.Generic;
using System.Data;

namespace GuiAutomationRange
{
    /// <summary>Row used by the standard WinForms DataGridView on tab 1.</summary>
    internal sealed class StandardRecord
    {
        public string EmployeeNo { get; set; }
        public string Name { get; set; }
        public string Department { get; set; }
        public string City { get; set; }
        public string Role { get; set; }
        public int Score { get; set; }
        public string Status { get; set; }
    }

    /// <summary>One of the 5x3 cells shown on the custom drawn table.</summary>
    internal sealed class CanvasOrder
    {
        public string OrderNo { get; set; }
        public string State { get; set; }
        public string Amount { get; set; }
    }

    /// <summary>
    /// All fake data used by the range. Keep this file free of UI code so the
    /// expected values can also be used by test scripts.
    /// </summary>
    internal static class TestData
    {
        public const string DemoAccount = "admin";
        public const string DemoPassword = "Admin@123";
        public const string CaptchaText = "A8B9";

        public const int CanvasPageCount = 3;
        public const int CanvasRowsPerPage = 5;

        public static readonly string[] Environments =
        {
            "开发环境 (DEV)",
            "测试环境 (TEST)",
            "预发布环境 (STAGING)",
            "生产环境 (PROD)"
        };

        public static readonly string[] DeleteTargets =
        {
            "#1001 · 华东渠道订单 · ¥1,280.00",
            "#1002 · 移动端续费 · ¥860.00",
            "#1003 · 企业版年费 · ¥2,399.50",
            "#1004 · 增值服务包 · ¥199.00"
        };

        private static readonly StandardRecord[] StandardRecords =
        {
            new StandardRecord { EmployeeNo = "EMP-1001", Name = "张伟", Department = "研发中心", City = "上海", Role = "测试工程师", Score = 95, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1002", Name = "李娜", Department = "产品设计", City = "北京", Role = "产品经理", Score = 88, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1003", Name = "王强", Department = "数据中心", City = "深圳", Role = "运维工程师", Score = 91, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1004", Name = "赵敏", Department = "质量保障", City = "杭州", Role = "QA 负责人", Score = 84, Status = "休假" },
            new StandardRecord { EmployeeNo = "EMP-1005", Name = "陈晨", Department = "客户成功", City = "成都", Role = "客户顾问", Score = 79, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1006", Name = "刘洋", Department = "研发中心", City = "广州", Role = "后端工程师", Score = 93, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1007", Name = "周婷", Department = "人力资源", City = "武汉", Role = "HRBP", Score = 87, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1008", Name = "吴磊", Department = "财务部", City = "南京", Role = "财务分析师", Score = 82, Status = "停职" },
            new StandardRecord { EmployeeNo = "EMP-1009", Name = "孙悦", Department = "产品设计", City = "西安", Role = "交互设计师", Score = 90, Status = "在职" },
            new StandardRecord { EmployeeNo = "EMP-1010", Name = "郑凯", Department = "数据中心", City = "苏州", Role = "SRE 工程师", Score = 89, Status = "在职" }
        };

        private static readonly CanvasOrder[] Orders =
        {
            new CanvasOrder { OrderNo = "ORD-240901", State = "已支付", Amount = "¥1,280.00" },
            new CanvasOrder { OrderNo = "ORD-240902", State = "待发货", Amount = "¥860.00" },
            new CanvasOrder { OrderNo = "ORD-240903", State = "已完成", Amount = "¥2,399.50" },
            new CanvasOrder { OrderNo = "ORD-240904", State = "退款中", Amount = "¥199.00" },
            new CanvasOrder { OrderNo = "ORD-240905", State = "已关闭", Amount = "¥0.00" },

            new CanvasOrder { OrderNo = "ORD-240906", State = "待支付", Amount = "¥3,450.00" },
            new CanvasOrder { OrderNo = "ORD-240907", State = "已发货", Amount = "¥749.90" },
            new CanvasOrder { OrderNo = "ORD-240908", State = "已完成", Amount = "¥1,099.00" },
            new CanvasOrder { OrderNo = "ORD-240909", State = "已取消", Amount = "¥0.00" },
            new CanvasOrder { OrderNo = "ORD-240910", State = "退款完成", Amount = "¥2,100.00" },

            new CanvasOrder { OrderNo = "ORD-240911", State = "已支付", Amount = "¥5,600.00" },
            new CanvasOrder { OrderNo = "ORD-240912", State = "待发货", Amount = "¥328.80" },
            new CanvasOrder { OrderNo = "ORD-240913", State = "已完成", Amount = "¥1,760.00" },
            new CanvasOrder { OrderNo = "ORD-240914", State = "退款中", Amount = "¥899.00" },
            new CanvasOrder { OrderNo = "ORD-240915", State = "已关闭", Amount = "¥0.00" }
        };

        private static readonly string[][] LogPages = BuildLogPages();

        public static DataTable CreateStandardTable()
        {
            DataTable table = new DataTable("StandardRecords");
            table.Columns.Add("工号", typeof(string));
            table.Columns.Add("姓名", typeof(string));
            table.Columns.Add("部门", typeof(string));
            table.Columns.Add("城市", typeof(string));
            table.Columns.Add("角色", typeof(string));
            table.Columns.Add("评分", typeof(int));
            table.Columns.Add("状态", typeof(string));

            foreach (StandardRecord record in StandardRecords)
            {
                table.Rows.Add(
                    record.EmployeeNo,
                    record.Name,
                    record.Department,
                    record.City,
                    record.Role,
                    record.Score,
                    record.Status);
            }
            table.AcceptChanges();
            return table;
        }

        public static IList<CanvasOrder> GetCanvasOrders(int pageIndex)
        {
            int safePage = Math.Max(0, Math.Min(CanvasPageCount - 1, pageIndex));
            List<CanvasOrder> result = new List<CanvasOrder>(CanvasRowsPerPage);
            int start = safePage * CanvasRowsPerPage;
            for (int i = 0; i < CanvasRowsPerPage; i++)
            {
                result.Add(Orders[start + i]);
            }
            return result;
        }

        public static string[] GetCanvasLog(int pageIndex)
        {
            int safePage = Math.Max(0, Math.Min(CanvasPageCount - 1, pageIndex));
            string[] source = LogPages[safePage];
            string[] copy = new string[source.Length];
            Array.Copy(source, copy, source.Length);
            return copy;
        }

        private static string[][] BuildLogPages()
        {
            string[][] pages = new string[CanvasPageCount][];
            for (int page = 0; page < CanvasPageCount; page++)
            {
                string[] lines = new string[20];
                lines[0] = string.Format("PAGE {0:00} / 03  ORDER PIPELINE EVENT LOG", page + 1);
                lines[1] = string.Format("[09:{0:00}:01] canvas.repaint page={1}", 40 + page, page + 1);
                lines[2] = string.Format("[09:{0:00}:02] accessibility.children=0", 40 + page);
                lines[3] = string.Format("[09:{0:00}:03] theme={1} jitter=on", 40 + page, page % 2 == 0 ? "light" : "dark");
                for (int i = 0; i < CanvasRowsPerPage; i++)
                {
                    CanvasOrder order = Orders[page * CanvasRowsPerPage + i];
                    lines[4 + i] = string.Format(
                        "[09:{0:00}:{1:00}] order {2} {3} {4}",
                        41 + page,
                        10 + i * 7,
                        order.OrderNo,
                        order.State,
                        order.Amount);
                }
                lines[9] = string.Format("[09:{0:00}:50] paginator.pageChanged -> {1}", 41 + page, page + 1);
                lines[10] = string.Format("[09:{0:00}:51] scrollbar.thumb=recalculated", 41 + page);
                lines[11] = "[09:42:02] ocr.hint = read text from pixels";
                lines[12] = "[09:42:03] uia.hint = panel only, no children";
                lines[13] = "[09:42:04] mouse.hint = hold button >= 300ms";
                lines[14] = string.Format("[09:42:05] page.buffer={0}/3", page + 1);
                lines[15] = "[09:42:06] captcha.render = A8B9 + noise";
                lines[16] = "[09:42:07] grid.render = 5 rows x 3 columns";
                lines[17] = "[09:42:08] hover.menu = file | edit | help";
                lines[18] = "[09:42:09] screenshot.diff = expected";
                lines[19] = string.Format("[09:42:10] END OF PAGE {0:00}", page + 1);
                pages[page] = lines;
            }
            return pages;
        }
    }
}
