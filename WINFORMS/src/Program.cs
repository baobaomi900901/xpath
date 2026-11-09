using System;
using System.Drawing;
using System.Windows.Forms;

namespace GuiAutomationRange
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.ThreadException += Application_ThreadException;
            Application.Run(new MainForm());
        }

        private static void Application_ThreadException(object sender, System.Threading.ThreadExceptionEventArgs e)
        {
            MessageBox.Show(
                "程序发生未处理异常：\r\n\r\n" + e.Exception,
                "GUI 自动化测试靶场",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
        }
    }
}
