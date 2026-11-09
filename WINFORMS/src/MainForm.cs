using System;
using System.Drawing;
using System.Windows.Forms;

namespace GuiAutomationRange
{
    internal sealed class MainForm : Form
    {
        public const string AppTitle = "GUI 自动化测试靶场 | Standard + Custom Canvas";

        private readonly TabControl _tabs;
        private readonly TabPage _standardTab;
        private readonly TabPage _canvasTab;
        private readonly CanvasRangePanel _canvas;

        public MainForm()
        {
            Text = AppTitle;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(1460, 940);
            MinimumSize = new Size(1240, 840);
            BackColor = Color.FromArgb(243, 246, 251);
            Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Regular, GraphicsUnit.Point);
            DoubleBuffered = true;
            KeyPreview = true;

            _tabs = new TabControl
            {
                Dock = DockStyle.Fill,
                Name = "tabRange",
                Font = new Font("Microsoft YaHei UI", 10f, FontStyle.Bold, GraphicsUnit.Point),
                Padding = new Point(18, 7)
            };

            _standardTab = new TabPage
            {
                Text = "Tab 1 · 标准控件靶场",
                BackColor = Color.FromArgb(243, 246, 251),
                UseVisualStyleBackColor = false,
                Padding = new Padding(0),
                AccessibleName = "标准控件靶场"
            };
            StandardRangePage standardPage = new StandardRangePage
            {
                Dock = DockStyle.Fill
            };
            _standardTab.Controls.Add(standardPage);

            _canvasTab = new TabPage
            {
                Text = "Tab 2 · 地狱自绘靶场",
                BackColor = Color.FromArgb(243, 246, 251),
                UseVisualStyleBackColor = false,
                Padding = new Padding(0)
            };
            _canvas = new CanvasRangePanel
            {
                Dock = DockStyle.Fill
            };
            _canvasTab.Controls.Add(_canvas);

            _tabs.TabPages.Add(_standardTab);
            _tabs.TabPages.Add(_canvasTab);
            _tabs.SelectedIndex = 0;
            _tabs.SelectedIndexChanged += Tabs_SelectedIndexChanged;

            Controls.Add(_tabs);
        }

        private void Tabs_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (_tabs.SelectedTab != _canvasTab)
            {
                return;
            }

            // Give the custom panel keyboard focus so the fake inputs receive
            // KeyPress without any child native control.
            BeginInvoke(new Action(delegate
            {
                _canvas.Focus();
            }));
        }

        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            if (_tabs.SelectedTab == _canvasTab && (keyData == Keys.F2 || keyData == Keys.F5))
            {
                _canvas.HandleHostShortcut(keyData);
                return true;
            }
            return base.ProcessCmdKey(ref msg, keyData);
        }
    }
}
