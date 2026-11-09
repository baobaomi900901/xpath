using System;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace GuiAutomationRange
{
    /// <summary>
    /// Tab 1: an ordinary WinForms page built only from native controls. Every
    /// interactive control has a stable Name so UIAutomation clients can use the
    /// AutomationId (the WinForms provider maps Control.Name to AutomationId).
    /// </summary>
    internal sealed class StandardRangePage : UserControl
    {
        private const int QueryDurationMs = 3000;

        private readonly TextBox _accountBox;
        private readonly TextBox _passwordBox;
        private readonly ComboBox _environmentCombo;
        private readonly CheckBox _rememberCheckBox;
        private readonly Button _loginButton;
        private readonly Button _clearLoginButton;
        private readonly Label _loginResultLabel;

        private readonly Button _queryButton;
        private readonly ProgressBar _queryProgress;
        private readonly Label _queryStatusLabel;
        private readonly Label _queryResultLabel;
        private readonly Timer _queryTimer;
        private readonly Stopwatch _queryWatch;

        private readonly Label _deleteTargetLabel;
        private readonly Button _deleteButton;
        private readonly Button _resetDeleteButton;
        private readonly Label _deleteStatusLabel;

        private readonly ListBox _eventList;
        private readonly DataGridView _recordsGrid;
        private readonly DataTable _recordsTable;

        private int _deleteIndex;

        public StandardRangePage()
        {
            DoubleBuffered = true;
            ResizeRedraw = true;
            AutoScroll = true;
            BackColor = Color.FromArgb(243, 246, 251);
            Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Regular, GraphicsUnit.Point);
            AccessibleName = "标准控件靶场";
            AccessibleDescription = "WinForms 原生控件、UIAutomation 树、模态对话框与可排序表格";

            _queryTimer = new Timer { Interval = 50 };
            _queryTimer.Tick += QueryTimer_Tick;
            _queryWatch = new Stopwatch();

            _accountBox = CreateTextBox("txtAccount", "账号", "登录账号，测试账号 admin", 24);
            _passwordBox = CreateTextBox("txtPassword", "密码", "登录密码，测试密码 Admin@123", 32);
            _passwordBox.PasswordChar = '*';
            _passwordBox.UseSystemPasswordChar = false;

            _environmentCombo = new ComboBox
            {
                Name = "cmbEnvironment",
                AccessibleName = "环境选择",
                AccessibleDescription = "选择登录目标环境",
                DropDownStyle = ComboBoxStyle.DropDownList,
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 4, 0, 4),
                Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Regular, GraphicsUnit.Point)
            };
            _environmentCombo.Items.AddRange(TestData.Environments);
            _environmentCombo.SelectedIndex = 0;

            _rememberCheckBox = new CheckBox
            {
                Name = "chkRemember",
                AccessibleName = "记住密码",
                AccessibleDescription = "仅本次运行有效",
                Text = "记住密码（仅本次运行）",
                AutoSize = true,
                Margin = new Padding(0, 3, 0, 2),
                Font = new Font("Microsoft YaHei UI", 9.2f, FontStyle.Regular, GraphicsUnit.Point)
            };

            _loginButton = MakeButton("登录", "btnLogin", 96, ButtonTone.Primary, "提交账号、密码和环境");
            _loginButton.Click += LoginButton_Click;
            _clearLoginButton = MakeButton("清空", "btnClearLogin", 78, ButtonTone.Secondary, "清空登录表单");
            _clearLoginButton.Click += ClearLoginButton_Click;

            _loginResultLabel = CreateStatusLabel("lblLoginResult", "登录结果", "测试账号：admin / Admin@123（环境任选）");
            _loginResultLabel.ForeColor = Color.FromArgb(100, 116, 139);

            _accountBox.KeyDown += LoginField_KeyDown;
            _passwordBox.KeyDown += LoginField_KeyDown;

            _queryButton = MakeButton("查询数据", "btnQuery", 128, ButtonTone.Primary, "启动 3 秒异步查询");
            _queryButton.Click += QueryButton_Click;
            _queryProgress = new ProgressBar
            {
                Name = "prgQuery",
                AccessibleName = "查询进度",
                AccessibleDescription = "异步查询进度条",
                Dock = DockStyle.Fill,
                Minimum = 0,
                Maximum = 100,
                Value = 0,
                Style = ProgressBarStyle.Continuous,
                Margin = new Padding(0, 4, 0, 4)
            };
            _queryStatusLabel = CreateStatusLabel("lblQueryStatus", "查询状态", "等待查询");
            _queryStatusLabel.Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Bold, GraphicsUnit.Point);
            _queryStatusLabel.ForeColor = Color.FromArgb(51, 65, 85);
            _queryResultLabel = CreateStatusLabel("lblQueryResult", "查询结果", "结果：--");
            _queryResultLabel.ForeColor = Color.FromArgb(100, 116, 139);

            _deleteTargetLabel = new Label
            {
                Name = "lblDeleteTarget",
                AccessibleName = "待删除记录",
                AutoSize = false,
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                Font = new Font("Microsoft YaHei UI", 9.4f, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(185, 28, 28),
                AutoEllipsis = true,
                Margin = new Padding(2, 2, 2, 2)
            };
            _deleteButton = MakeButton("删除记录...", "btnDelete", 118, ButtonTone.Danger, "打开自定义模态确认框");
            _deleteButton.Click += DeleteButton_Click;
            _resetDeleteButton = MakeButton("重置列表", "btnResetDelete", 100, ButtonTone.Secondary, "恢复被删除的演示记录");
            _resetDeleteButton.Click += ResetDeleteButton_Click;
            _deleteStatusLabel = CreateStatusLabel("lblDeleteStatus", "删除状态", "尚未执行删除");
            _deleteStatusLabel.ForeColor = Color.FromArgb(100, 116, 139);

            _eventList = new ListBox
            {
                Name = "lstEventLog",
                AccessibleName = "运行日志",
                AccessibleDescription = "记录登录、查询和删除事件",
                Dock = DockStyle.Fill,
                BorderStyle = BorderStyle.FixedSingle,
                IntegralHeight = false,
                Font = new Font("Microsoft YaHei UI", 8.8f, FontStyle.Regular, GraphicsUnit.Point),
                BackColor = Color.FromArgb(248, 250, 252),
                ForeColor = Color.FromArgb(51, 65, 85)
            };

            _recordsTable = TestData.CreateStandardTable();
            _recordsGrid = CreateRecordsGrid();

            BuildLayout();
            UpdateDeleteTargetLabel();
            AddEvent("标准控件页就绪 · 10 条测试数据 · 表头可排序");
        }

        private void BuildLayout()
        {
            TableLayoutPanel root = new TableLayoutPanel
            {
                Dock = DockStyle.Top,
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                ColumnCount = 2,
                RowCount = 4,
                Padding = new Padding(12, 10, 12, 14),
                BackColor = Color.FromArgb(243, 246, 251)
            };
            root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));
            root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 82f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 260f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 204f));
            root.RowStyles.Add(new RowStyle(SizeType.Absolute, 318f));

            Control header = CreateHeader();
            root.Controls.Add(header, 0, 0);
            root.SetColumnSpan(header, 2);

            GroupBox loginGroup = CreateGroupBox("模块 1 · 复杂登录表单（原生控件）");            loginGroup.Controls.Add(CreateLoginContent());
            loginGroup.Margin = new Padding(6, 5, 6, 5);
            root.Controls.Add(loginGroup, 0, 1);

            GroupBox queryGroup = CreateGroupBox("模块 2 · 异步加载区域（3 秒查询）");
            queryGroup.Controls.Add(CreateQueryContent());
            queryGroup.Margin = new Padding(6, 5, 6, 5);
            root.Controls.Add(queryGroup, 1, 1);

            GroupBox dialogGroup = CreateGroupBox("模块 3 · 多级弹窗（确认 → 成功）");
            dialogGroup.Controls.Add(CreateDialogContent());
            dialogGroup.Margin = new Padding(6, 5, 6, 5);
            root.Controls.Add(dialogGroup, 0, 2);

            GroupBox logGroup = CreateGroupBox("运行日志（标准 ListBox）");
            logGroup.Controls.Add(_eventList);
            logGroup.Margin = new Padding(6, 5, 6, 5);
            root.Controls.Add(logGroup, 1, 2);

            GroupBox tableGroup = CreateGroupBox("模块 4 · 标准数据表格（10 条 · 单击表头升序 / 降序）");
            tableGroup.Controls.Add(CreateTableContent());
            tableGroup.Margin = new Padding(6, 5, 6, 5);
            root.Controls.Add(tableGroup, 0, 3);
            root.SetColumnSpan(tableGroup, 2);

            Controls.Add(root);
        }

        private Control CreateHeader()
        {
            TableLayoutPanel header = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 1,
                BackColor = Color.FromArgb(20, 30, 49),
                Margin = new Padding(0)
            };
            header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
            header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 330f));

            Panel textPanel = new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(20, 30, 49) };
            Label kicker = new Label
            {
                Text = "TAB 1 / STANDARD UI",
                ForeColor = Color.FromArgb(96, 165, 250),
                Font = new Font("Segoe UI", 7.2f, FontStyle.Bold, GraphicsUnit.Point),
                AutoSize = true,
                Location = new Point(18, 2)
            };
            Label title = new Label
            {
                Text = "标准控件靶场",
                ForeColor = Color.White,
                Font = new Font("Microsoft YaHei UI", 13.5f, FontStyle.Bold, GraphicsUnit.Point),
                AutoSize = true,
                Location = new Point(16, 20)
            };
            Label subtitle = new Label
            {
                Text = "原生 TextBox / ComboBox / CheckBox / Button / ProgressBar / DataGridView · UIAutomation 可遍历",
                ForeColor = Color.FromArgb(174, 190, 214),
                Font = new Font("Microsoft YaHei UI", 8f, FontStyle.Regular, GraphicsUnit.Point),
                AutoSize = true,
                Location = new Point(19, 58)
            };
            textPanel.Controls.Add(kicker);
            textPanel.Controls.Add(title);
            textPanel.Controls.Add(subtitle);

            Label badge = new Label
            {
                Dock = DockStyle.Fill,
                Text = "UIA READY  ·  STABLE IDs",
                TextAlign = ContentAlignment.MiddleRight,
                Padding = new Padding(0, 0, 20, 0),
                ForeColor = Color.FromArgb(134, 239, 172),
                Font = new Font("Segoe UI", 7.8f, FontStyle.Bold, GraphicsUnit.Point)
            };

            header.Controls.Add(textPanel, 0, 0);
            header.Controls.Add(badge, 1, 0);
            return header;
        }

        private Control CreateLoginContent()
        {
            TableLayoutPanel grid = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 6,
                Padding = new Padding(2, 3, 2, 2)
            };
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 76f));
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 37f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 37f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 37f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 29f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 39f));
            grid.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));

            grid.Controls.Add(CreateFieldLabel("账号"), 0, 0);
            grid.Controls.Add(_accountBox, 1, 0);
            grid.Controls.Add(CreateFieldLabel("密码"), 0, 1);
            grid.Controls.Add(_passwordBox, 1, 1);
            grid.Controls.Add(CreateFieldLabel("环境"), 0, 2);
            grid.Controls.Add(_environmentCombo, 1, 2);
            grid.Controls.Add(_rememberCheckBox, 0, 3);
            grid.SetColumnSpan(_rememberCheckBox, 2);

            FlowLayoutPanel actions = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = false,
                Margin = new Padding(76, 2, 0, 0),
                Padding = new Padding(0)
            };
            actions.Controls.Add(_loginButton);
            actions.Controls.Add(_clearLoginButton);
            grid.Controls.Add(actions, 0, 4);
            grid.SetColumnSpan(actions, 2);

            grid.Controls.Add(_loginResultLabel, 0, 5);
            grid.SetColumnSpan(_loginResultLabel, 2);
            return grid;
        }

        private Control CreateQueryContent()
        {
            TableLayoutPanel grid = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 1,
                RowCount = 6,
                Padding = new Padding(4, 4, 4, 2)
            };
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 34f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 44f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 26f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 30f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 28f));
            grid.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));

            Label intro = new Label
            {
                Text = "点击后按钮立即禁用，ProgressBar 运行 3 秒，然后恢复按钮并在状态标签显示“查询成功”。",
                ForeColor = Color.FromArgb(100, 116, 139),
                AutoSize = false,
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                Font = new Font("Microsoft YaHei UI", 8.6f, FontStyle.Regular, GraphicsUnit.Point),
                AutoEllipsis = true
            };

            FlowLayoutPanel queryActions = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = false,
                Padding = new Padding(0, 3, 0, 0)
            };
            queryActions.Controls.Add(_queryButton);

            Label timerHint = new Label
            {
                Text = "System.Windows.Forms.Timer · 50 ms tick",
                ForeColor = Color.FromArgb(148, 163, 184),
                AutoSize = true,
                Margin = new Padding(12, 10, 0, 0),
                Font = new Font("Segoe UI", 8f, FontStyle.Regular, GraphicsUnit.Point)
            };
            queryActions.Controls.Add(timerHint);

            grid.Controls.Add(intro, 0, 0);
            grid.Controls.Add(queryActions, 0, 1);
            grid.Controls.Add(_queryProgress, 0, 2);
            grid.Controls.Add(_queryStatusLabel, 0, 3);
            grid.Controls.Add(_queryResultLabel, 0, 4);

            Label footer = new Label
            {
                Text = "自动化检查点：Invoke 后读取 btnQuery.IsEnabled = false，等待 3 秒后恢复为 true。",
                ForeColor = Color.FromArgb(148, 163, 184),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.TopLeft,
                Font = new Font("Microsoft YaHei UI", 8.2f, FontStyle.Regular, GraphicsUnit.Point)
            };
            grid.Controls.Add(footer, 0, 5);
            return grid;
        }

        private Control CreateDialogContent()
        {
            TableLayoutPanel grid = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 1,
                RowCount = 5,
                Padding = new Padding(4, 3, 4, 2)
            };
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 25f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 36f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 40f));
            grid.RowStyles.Add(new RowStyle(SizeType.Absolute, 28f));
            grid.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));

            Label caption = new Label
            {
                Text = "当前待删除记录：",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                ForeColor = Color.FromArgb(71, 85, 105),
                Font = new Font("Microsoft YaHei UI", 8.6f, FontStyle.Regular, GraphicsUnit.Point)
            };

            FlowLayoutPanel actions = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = false,
                Padding = new Padding(0, 3, 0, 0)
            };
            actions.Controls.Add(_deleteButton);
            actions.Controls.Add(_resetDeleteButton);

            grid.Controls.Add(caption, 0, 0);
            grid.Controls.Add(_deleteTargetLabel, 0, 1);
            grid.Controls.Add(actions, 0, 2);
            grid.Controls.Add(_deleteStatusLabel, 0, 3);

            Label hint = new Label
            {
                Text = "流程：单击“删除记录...” → 自定义 Form.ShowDialog 确认 → 标准 MessageBox 成功提示。取消只关闭第一层。",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.TopLeft,
                ForeColor = Color.FromArgb(148, 163, 184),
                Font = new Font("Microsoft YaHei UI", 8.2f, FontStyle.Regular, GraphicsUnit.Point)
            };
            grid.Controls.Add(hint, 0, 4);
            return grid;
        }

        private Control CreateTableContent()
        {
            Panel container = new Panel { Dock = DockStyle.Fill, BackColor = Color.White };
            container.Controls.Add(_recordsGrid);
            return container;
        }

        private DataGridView CreateRecordsGrid()
        {
            DataGridView grid = new DataGridView
            {
                Name = "dgvRecords",
                AccessibleName = "测试数据表格",
                AccessibleDescription = "10 行标准 DataGridView 测试数据，可点击表头排序",
                Dock = DockStyle.Fill,
                AutoGenerateColumns = false,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                AllowUserToResizeRows = false,
                ReadOnly = true,
                RowHeadersVisible = false,
                MultiSelect = false,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                BorderStyle = BorderStyle.None,
                BackgroundColor = Color.White,
                GridColor = Color.FromArgb(226, 232, 240),
                CellBorderStyle = DataGridViewCellBorderStyle.SingleHorizontal,
                ColumnHeadersHeight = 34,
                ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing,
                EnableHeadersVisualStyles = false,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                ClipboardCopyMode = DataGridViewClipboardCopyMode.EnableAlwaysIncludeHeaderText,
                Font = new Font("Microsoft YaHei UI", 8.3f, FontStyle.Regular, GraphicsUnit.Point)
            };
            grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(219, 234, 254);
            grid.DefaultCellStyle.SelectionForeColor = Color.FromArgb(15, 23, 42);
            grid.DefaultCellStyle.Padding = new Padding(6, 0, 6, 0);
            grid.AlternatingRowsDefaultCellStyle.BackColor = Color.FromArgb(248, 250, 252);
            grid.RowTemplate.Height = 23;
            grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(30, 58, 95);
            grid.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
            grid.ColumnHeadersDefaultCellStyle.SelectionBackColor = Color.FromArgb(30, 58, 95);
            grid.ColumnHeadersDefaultCellStyle.SelectionForeColor = Color.White;
            grid.ColumnHeadersDefaultCellStyle.Font = new Font("Microsoft YaHei UI", 8.5f, FontStyle.Bold, GraphicsUnit.Point);
            grid.ColumnHeadersDefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleLeft;

            AddGridColumn(grid, "工号", "工号", 110, 90);
            AddGridColumn(grid, "姓名", "姓名", 90, 70);
            AddGridColumn(grid, "部门", "部门", 130, 90);
            AddGridColumn(grid, "城市", "城市", 90, 70);
            AddGridColumn(grid, "角色", "角色", 150, 100);
            AddGridColumn(grid, "评分", "评分", 80, 60);
            AddGridColumn(grid, "状态", "状态", 90, 70);

            grid.DataSource = _recordsTable;
            grid.ColumnHeaderMouseClick += RecordsGrid_ColumnHeaderMouseClick;
            return grid;
        }

        private static void AddGridColumn(DataGridView grid, string propertyName, string headerText, float fillWeight, int minimumWidth)
        {
            DataGridViewTextBoxColumn column = new DataGridViewTextBoxColumn
            {
                DataPropertyName = propertyName,
                HeaderText = headerText,
                Name = "col" + propertyName,
                FillWeight = fillWeight,
                MinimumWidth = minimumWidth,
                SortMode = DataGridViewColumnSortMode.Programmatic,
                ReadOnly = true
            };
            grid.Columns.Add(column);
        }

        private void RecordsGrid_ColumnHeaderMouseClick(object sender, DataGridViewCellMouseEventArgs e)
        {
            if (e.ColumnIndex < 0 || e.ColumnIndex >= _recordsGrid.Columns.Count)
            {
                return;
            }

            DataGridViewColumn column = _recordsGrid.Columns[e.ColumnIndex];
            string propertyName = column.DataPropertyName;
            if (string.IsNullOrEmpty(propertyName))
            {
                return;
            }

            ListSortDirection direction = ListSortDirection.Ascending;
            if (column.HeaderCell.SortGlyphDirection == SortOrder.Ascending)
            {
                direction = ListSortDirection.Descending;
            }

            foreach (DataGridViewColumn item in _recordsGrid.Columns)
            {
                item.HeaderCell.SortGlyphDirection = SortOrder.None;
            }

            _recordsTable.DefaultView.Sort = "[" + propertyName + "] " +
                (direction == ListSortDirection.Ascending ? "ASC" : "DESC");
            column.HeaderCell.SortGlyphDirection = direction == ListSortDirection.Ascending
                ? SortOrder.Ascending
                : SortOrder.Descending;
            AddEvent("表格排序：" + column.HeaderText + " " + (direction == ListSortDirection.Ascending ? "升序" : "降序"));
        }

        private void LoginButton_Click(object sender, EventArgs e)
        {
            string account = _accountBox.Text.Trim();
            string password = _passwordBox.Text;
            string environment = _environmentCombo.SelectedItem as string ?? "(未选择)";

            if (account.Length == 0 || password.Length == 0)
            {
                SetLoginResult("请输入账号和密码。", true);
                AddEvent("登录校验失败：账号或密码为空");
                return;
            }

            if (!string.Equals(account, TestData.DemoAccount, StringComparison.Ordinal) ||
                !string.Equals(password, TestData.DemoPassword, StringComparison.Ordinal))
            {
                SetLoginResult("账号或密码错误。使用 admin / Admin@123。", true);
                AddEvent("登录校验失败：凭据错误");
                return;
            }

            string suffix = _rememberCheckBox.Checked ? " · 已记住本次运行" : string.Empty;
            SetLoginResult("登录成功：admin（管理员）· " + environment + suffix, false);
            AddEvent("登录成功：admin · " + environment);
        }

        private void ClearLoginButton_Click(object sender, EventArgs e)
        {
            _accountBox.Clear();
            _passwordBox.Clear();
            _environmentCombo.SelectedIndex = 0;
            _rememberCheckBox.Checked = false;
            _loginResultLabel.Text = "已清空登录表单。测试账号：admin / Admin@123";
            _loginResultLabel.ForeColor = Color.FromArgb(100, 116, 139);
            AddEvent("登录表单已清空");
            _accountBox.Focus();
        }

        private void LoginField_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                e.SuppressKeyPress = true;
                LoginButton_Click(sender, EventArgs.Empty);
            }
        }

        private void SetLoginResult(string text, bool error)
        {
            _loginResultLabel.Text = text;
            _loginResultLabel.ForeColor = error ? Color.FromArgb(185, 28, 28) : Color.FromArgb(4, 120, 87);
        }

        private void QueryButton_Click(object sender, EventArgs e)
        {
            if (!_queryButton.Enabled || _queryTimer.Enabled)
            {
                return;
            }

            _queryButton.Enabled = false;
            _queryButton.Text = "查询中...";
            _queryProgress.Value = 0;
            _queryStatusLabel.Text = "正在查询... 0%";
            _queryStatusLabel.ForeColor = Color.FromArgb(37, 99, 235);
            _queryResultLabel.Text = "结果：--";
            _queryWatch.Restart();
            _queryTimer.Start();
            AddEvent("异步查询启动：btnQuery 已禁用");
        }

        private void QueryTimer_Tick(object sender, EventArgs e)
        {
            long elapsed = _queryWatch.ElapsedMilliseconds;
            int percent = (int)Math.Min(100L, (elapsed * 100L) / QueryDurationMs);
            if (percent != _queryProgress.Value)
            {
                _queryProgress.Value = percent;
            }
            _queryStatusLabel.Text = "正在查询... " + percent + "%";

            if (elapsed < QueryDurationMs)
            {
                return;
            }

            _queryTimer.Stop();
            _queryWatch.Stop();
            _queryProgress.Value = 100;
            _queryButton.Enabled = true;
            _queryButton.Text = "查询数据";
            _queryStatusLabel.Text = "查询成功";
            _queryStatusLabel.ForeColor = Color.FromArgb(4, 120, 87);
            _queryResultLabel.Text = "结果：返回 10 条测试记录 · 耗时 3.0 秒";
            AddEvent("异步查询完成：查询成功（3.0s）");
        }

        private void DeleteButton_Click(object sender, EventArgs e)
        {
            if (_deleteIndex >= TestData.DeleteTargets.Length)
            {
                MessageBox.Show(
                    FindForm(),
                    "没有待删除的演示记录，请先点击“重置列表”。",
                    "无可删除记录",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);
                return;
            }

            string target = TestData.DeleteTargets[_deleteIndex];
            using (ConfirmDeleteDialog dialog = new ConfirmDeleteDialog(target))
            {
                DialogResult result = dialog.ShowDialog(FindForm());
                if (result != DialogResult.OK)
                {
                    _deleteStatusLabel.Text = "已取消删除：" + target;
                    _deleteStatusLabel.ForeColor = Color.FromArgb(100, 116, 139);
                    AddEvent("删除已取消：" + target);
                    return;
                }
            }

            _deleteIndex++;
            _deleteStatusLabel.Text = "已删除：" + target;
            _deleteStatusLabel.ForeColor = Color.FromArgb(4, 120, 87);
            UpdateDeleteTargetLabel();
            AddEvent("已确认删除：" + target);

            MessageBox.Show(
                FindForm(),
                "记录 " + target + " 已删除。\r\n\r\n这是确认框之后的第二层成功提示。",
                "删除成功",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);
        }

        private void ResetDeleteButton_Click(object sender, EventArgs e)
        {
            _deleteIndex = 0;
            _deleteStatusLabel.Text = "删除列表已重置";
            _deleteStatusLabel.ForeColor = Color.FromArgb(100, 116, 139);
            UpdateDeleteTargetLabel();
            AddEvent("删除演示列表已重置");
        }

        private void UpdateDeleteTargetLabel()
        {
            if (_deleteIndex >= TestData.DeleteTargets.Length)
            {
                _deleteTargetLabel.Text = "没有待删除记录（点击“重置列表”恢复）";
                _deleteTargetLabel.ForeColor = Color.FromArgb(100, 116, 139);
                _deleteButton.Enabled = false;
                return;
            }

            _deleteTargetLabel.Text = TestData.DeleteTargets[_deleteIndex];
            _deleteTargetLabel.ForeColor = Color.FromArgb(185, 28, 28);
            _deleteButton.Enabled = true;
        }

        private void AddEvent(string message)
        {
            if (_eventList == null)
            {
                return;
            }

            _eventList.Items.Insert(0, string.Format("{0:HH:mm:ss}  {1}", DateTime.Now, message));
            while (_eventList.Items.Count > 40)
            {
                _eventList.Items.RemoveAt(_eventList.Items.Count - 1);
            }
        }

        private static TextBox CreateTextBox(string name, string accessibleName, string description, int maxLength)
        {
            return new TextBox
            {
                Name = name,
                AccessibleName = accessibleName,
                AccessibleDescription = description,
                Dock = DockStyle.Fill,
                MaxLength = maxLength,
                Margin = new Padding(0, 4, 0, 4),
                Font = new Font("Microsoft YaHei UI", 9.5f, FontStyle.Regular, GraphicsUnit.Point)
            };
        }

        private static Label CreateFieldLabel(string text)
        {
            return new Label
            {
                Text = text,
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                ForeColor = Color.FromArgb(51, 65, 85),
                Font = new Font("Microsoft YaHei UI", 9f, FontStyle.Bold, GraphicsUnit.Point)
            };
        }

        private static Label CreateStatusLabel(string name, string accessibleName, string text)
        {
            return new Label
            {
                Name = name,
                AccessibleName = accessibleName,
                Text = text,
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                AutoEllipsis = true,
                Font = new Font("Microsoft YaHei UI", 8.8f, FontStyle.Regular, GraphicsUnit.Point)
            };
        }

        private static GroupBox CreateGroupBox(string text)
        {
            return new GroupBox
            {
                Text = text,
                Dock = DockStyle.Fill,
                BackColor = Color.White,
                ForeColor = Color.FromArgb(30, 41, 59),
                Font = new Font("Microsoft YaHei UI", 10f, FontStyle.Bold, GraphicsUnit.Point),
                Padding = new Padding(10, 8, 10, 8)
            };
        }

        private enum ButtonTone
        {
            Primary,
            Secondary,
            Danger
        }

        private static Button MakeButton(string text, string name, int width, ButtonTone tone, string description)
        {
            Button button = new Button
            {
                Text = text,
                Name = name,
                AccessibleName = text,
                AccessibleDescription = description,
                Width = width,
                Height = 32,
                Margin = new Padding(0, 0, 8, 0),
                FlatStyle = FlatStyle.Flat,
                UseVisualStyleBackColor = false,
                Font = new Font("Microsoft YaHei UI", 9f, FontStyle.Bold, GraphicsUnit.Point),
                Cursor = Cursors.Hand
            };

            if (tone == ButtonTone.Primary)
            {
                button.BackColor = Color.FromArgb(37, 99, 235);
                button.ForeColor = Color.White;
                button.FlatAppearance.BorderSize = 0;
            }
            else if (tone == ButtonTone.Danger)
            {
                button.BackColor = Color.FromArgb(185, 28, 28);
                button.ForeColor = Color.White;
                button.FlatAppearance.BorderSize = 0;
            }
            else
            {
                button.BackColor = Color.FromArgb(241, 245, 249);
                button.ForeColor = Color.FromArgb(30, 41, 59);
                button.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
                button.FlatAppearance.BorderSize = 1;
            }

            return button;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _queryTimer.Stop();
                _queryTimer.Dispose();
                _queryWatch.Stop();
            }
            base.Dispose(disposing);
        }
    }
}
