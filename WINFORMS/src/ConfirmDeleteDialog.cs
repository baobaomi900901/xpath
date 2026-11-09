using System;
using System.Drawing;
using System.Windows.Forms;

namespace GuiAutomationRange
{
    /// <summary>
    /// Modal confirmation used by tab 1. It intentionally uses standard WinForms
    /// controls so a UIAutomation client can locate the nested dialog and buttons.
    /// </summary>
    internal sealed class ConfirmDeleteDialog : Form
    {
        private readonly Label _messageLabel;

        public ConfirmDeleteDialog(string recordText)
        {
            Text = "确认删除";
            StartPosition = FormStartPosition.CenterParent;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            ShowIcon = false;
            ClientSize = new Size(510, 232);
            BackColor = Color.White;
            Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Regular, GraphicsUnit.Point);
            AutoScaleMode = AutoScaleMode.Font;
            Padding = new Padding(18);

            TableLayoutPanel root = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 5,
                BackColor = Color.White
            };
            root.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 58f));
            root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 42f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 34f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 46f));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 44f));

            Label icon = new Label
            {
                Text = "⚠",
                Font = new Font("Segoe UI Symbol", 24f, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(217, 119, 6),
                TextAlign = ContentAlignment.MiddleCenter,
                Dock = DockStyle.Fill,
                AccessibleName = "警告图标",
                AccessibleRole = AccessibleRole.StaticText
            };

            Label title = new Label
            {
                Text = "确认删除这条测试记录？",
                Font = new Font("Microsoft YaHei UI", 13f, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 32, 48),
                TextAlign = ContentAlignment.MiddleLeft,
                Dock = DockStyle.Fill,
                AccessibleName = "确认删除标题"
            };

            _messageLabel = new Label
            {
                Text = recordText,
                Font = new Font("Microsoft YaHei UI", 10.5f, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(185, 28, 28),
                TextAlign = ContentAlignment.MiddleLeft,
                Dock = DockStyle.Fill,
                AutoEllipsis = true,
                AccessibleName = "待删除记录"
            };

            Label hint = new Label
            {
                Text = "这是自定义模态确认框（Form.ShowDialog）。确认后将再弹出一个标准 MessageBox 成功提示。\r\n自动化脚本需要先处理此对话框，再处理下一层提示。",
                ForeColor = Color.FromArgb(90, 102, 122),
                TextAlign = ContentAlignment.TopLeft,
                Dock = DockStyle.Fill,
                Font = new Font("Microsoft YaHei UI", 8.8f, FontStyle.Regular, GraphicsUnit.Point),
                AccessibleName = "删除提示"
            };

            FlowLayoutPanel actions = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.RightToLeft,
                WrapContents = false,
                Padding = new Padding(0, 7, 0, 0),
                BackColor = Color.White
            };

            Button confirm = new Button
            {
                Text = "确认删除",
                DialogResult = DialogResult.OK,
                Width = 112,
                Height = 34,
                Name = "btnConfirmDelete",
                AccessibleName = "确认删除",
                AccessibleDescription = "确认并关闭模态框",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(185, 28, 28),
                ForeColor = Color.White,
                Font = new Font("Microsoft YaHei UI", 9.2f, FontStyle.Bold, GraphicsUnit.Point)
            };
            confirm.FlatAppearance.BorderSize = 0;

            Button cancel = new Button
            {
                Text = "取消",
                DialogResult = DialogResult.Cancel,
                Width = 92,
                Height = 34,
                Name = "btnCancelDelete",
                AccessibleName = "取消",
                AccessibleDescription = "取消删除并关闭模态框",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(241, 245, 249),
                ForeColor = Color.FromArgb(30, 41, 59)
            };
            cancel.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            cancel.FlatAppearance.BorderSize = 1;

            actions.Controls.Add(confirm);
            actions.Controls.Add(cancel);

            root.Controls.Add(icon, 0, 0);
            root.SetRowSpan(icon, 2);
            root.Controls.Add(title, 1, 0);
            root.Controls.Add(_messageLabel, 1, 1);
            root.Controls.Add(hint, 0, 2);
            root.SetColumnSpan(hint, 2);
            root.SetRowSpan(hint, 2);
            root.Controls.Add(actions, 0, 4);
            root.SetColumnSpan(actions, 2);

            Controls.Add(root);
            AcceptButton = confirm;
            CancelButton = cancel;
        }
    }
}
