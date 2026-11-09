using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;

namespace GuiAutomationRange
{
    /// <summary>
    /// Tab 2: a single owner-drawn panel. It has no child controls, no
    /// AccessibleName and no AccessibleRole, so UIAutomation and MSAA can only
    /// see the empty panel. Every scene is rendered with GDI+ and every hit test
    /// is implemented by hand.
    /// </summary>
    internal sealed class CanvasRangePanel : Panel
    {
        private const int JitterRange = 30;
        private const int AntiBounceMs = 300;
        private const int TableRowCount = 5;
        private const int LogLineHeight = 20;

        private static readonly string[] MenuLabels = { "文件", "编辑", "帮助" };
        private static readonly string[][] MenuItems =
        {
            new[] { "重置会话", "随机化坐标  F5", "退出程序" },
            new[] { "复制账号", "粘贴账号", "清空事件日志" },
            new[] { "快捷键说明", "关于靶场" }
        };

        private static readonly CanvasPalette LightTheme = new CanvasPalette
        {
            Dark = false,
            Background = Color.FromArgb(243, 246, 251),
            BackgroundAlt = Color.FromArgb(232, 238, 248),
            Surface = Color.White,
            SurfaceAlt = Color.FromArgb(248, 250, 252),
            Border = Color.FromArgb(216, 226, 240),
            Text = Color.FromArgb(20, 32, 51),
            Muted = Color.FromArgb(100, 116, 139),
            Accent = Color.FromArgb(37, 99, 235),
            Accent2 = Color.FromArgb(124, 58, 237),
            AccentText = Color.White,
            Input = Color.FromArgb(248, 250, 252),
            Grid = Color.FromArgb(221, 229, 242),
            Success = Color.FromArgb(4, 120, 87),
            Warning = Color.FromArgb(180, 83, 9),
            Danger = Color.FromArgb(185, 28, 28),
            MenuSurface = Color.White,
            MenuHover = Color.FromArgb(239, 246, 255),
            Shadow = Color.FromArgb(38, 15, 23, 42),
            HeaderLine = Color.FromArgb(226, 232, 240)
        };

        private static readonly CanvasPalette DarkTheme = new CanvasPalette
        {
            Dark = true,
            Background = Color.FromArgb(11, 18, 32),
            BackgroundAlt = Color.FromArgb(17, 27, 46),
            Surface = Color.FromArgb(18, 28, 46),
            SurfaceAlt = Color.FromArgb(24, 36, 58),
            Border = Color.FromArgb(43, 58, 85),
            Text = Color.FromArgb(234, 241, 255),
            Muted = Color.FromArgb(148, 163, 184),
            Accent = Color.FromArgb(79, 140, 255),
            Accent2 = Color.FromArgb(167, 139, 250),
            AccentText = Color.White,
            Input = Color.FromArgb(15, 25, 41),
            Grid = Color.FromArgb(38, 52, 77),
            Success = Color.FromArgb(52, 211, 153),
            Warning = Color.FromArgb(251, 191, 36),
            Danger = Color.FromArgb(248, 113, 113),
            MenuSurface = Color.FromArgb(24, 36, 58),
            MenuHover = Color.FromArgb(34, 52, 86),
            Shadow = Color.FromArgb(120, 0, 0, 0),
            HeaderLine = Color.FromArgb(31, 44, 66)
        };

        private readonly Timer _caretTimer;
        private readonly Timer _animationTimer;
        private readonly Random _random;
        private readonly Dictionary<string, Point> _jitter;
        private readonly List<CanvasButton> _buttons;
        private readonly List<string> _events;
        private readonly Rectangle[] _menuBarRects;

        private readonly Font _fontOverline;
        private readonly Font _fontTitle;
        private readonly Font _fontSubtitle;
        private readonly Font _fontCardTitle;
        private readonly Font _fontCardHint;
        private readonly Font _fontBody;
        private readonly Font _fontSmall;
        private readonly Font _fontTiny;
        private readonly Font _fontButton;
        private readonly Font _fontTableHeader;
        private readonly Font _fontTable;
        private readonly Font _fontLog;
        private readonly Font _fontCaptcha;
        private readonly Font _fontMenu;

        private CanvasPalette _palette;

        private Rectangle _loginCard;
        private Rectangle _tableCard;
        private Rectangle _pageCard;
        private Rectangle _statusCard;

        private Rectangle _accountRect;
        private Rectangle _passwordRect;
        private Rectangle _captchaInputRect;
        private Rectangle _captchaVisualRect;
        private Rectangle _tableHeaderRect;
        private Rectangle[] _tableRowRects;
        private Rectangle _logViewport;
        private Rectangle _scrollUpRect;
        private Rectangle _scrollDownRect;
        private Rectangle _scrollTrackRect;
        private Rectangle _scrollThumbRect;

        private InputField _focusedField;
        private bool _caretVisible;
        private string _accountText;
        private string _passwordText;
        private string _captchaText;

        private int _pageIndex;
        private int _scrollOffset;
        private int _visibleLogLines;
        private int _totalLogLines;
        private bool _draggingThumb;
        private int _dragThumbOffset;

        private int _activeMenu;
        private int _hoverMenuItem;
        private string _hoverButtonId;
        private CanvasButton _pressedButton;
        private DateTime _pressStartUtc;

        private string _statusText;
        private StatusKind _statusKind;
        private string _lastAction;
        private int _captchaSeed;
        private bool _layoutDirty;

        public CanvasRangePanel()
        {
            SetStyle(
                ControlStyles.UserPaint |
                ControlStyles.AllPaintingInWmPaint |
                ControlStyles.OptimizedDoubleBuffer |
                ControlStyles.ResizeRedraw |
                ControlStyles.Selectable,
                true);
            UpdateStyles();
            DoubleBuffered = true;
            TabStop = true;
            BackColor = LightTheme.Background;
            Cursor = Cursors.Default;

            _palette = LightTheme;
            _random = new Random(unchecked(Environment.TickCount * 397 ^ Guid.NewGuid().GetHashCode()));
            _captchaSeed = _random.Next();
            _jitter = new Dictionary<string, Point>();
            _buttons = new List<CanvasButton>();
            _events = new List<string>();
            _menuBarRects = new Rectangle[MenuLabels.Length];
            _tableRowRects = new Rectangle[TableRowCount];

            _fontOverline = new Font("Segoe UI", 7.8f, FontStyle.Bold, GraphicsUnit.Point);
            _fontTitle = new Font("Microsoft YaHei UI", 16.5f, FontStyle.Bold, GraphicsUnit.Point);
            _fontSubtitle = new Font("Microsoft YaHei UI", 8.4f, FontStyle.Regular, GraphicsUnit.Point);
            _fontCardTitle = new Font("Microsoft YaHei UI", 10.6f, FontStyle.Bold, GraphicsUnit.Point);
            _fontCardHint = new Font("Microsoft YaHei UI", 7.6f, FontStyle.Regular, GraphicsUnit.Point);
            _fontBody = new Font("Microsoft YaHei UI", 9.2f, FontStyle.Regular, GraphicsUnit.Point);
            _fontSmall = new Font("Microsoft YaHei UI", 8.4f, FontStyle.Regular, GraphicsUnit.Point);
            _fontTiny = new Font("Microsoft YaHei UI", 7.4f, FontStyle.Regular, GraphicsUnit.Point);
            _fontButton = new Font("Microsoft YaHei UI", 9.2f, FontStyle.Bold, GraphicsUnit.Point);
            _fontTableHeader = new Font("Microsoft YaHei UI", 8.7f, FontStyle.Bold, GraphicsUnit.Point);
            _fontTable = new Font("Microsoft YaHei UI", 8.9f, FontStyle.Regular, GraphicsUnit.Point);
            _fontLog = new Font("Microsoft YaHei UI", 8f, FontStyle.Regular, GraphicsUnit.Point);
            _fontCaptcha = new Font("Consolas", 11.5f, FontStyle.Bold, GraphicsUnit.Point);
            _fontMenu = new Font("Microsoft YaHei UI", 9.2f, FontStyle.Regular, GraphicsUnit.Point);

            _accountText = string.Empty;
            _passwordText = string.Empty;
            _captchaText = string.Empty;
            _focusedField = InputField.None;
            _caretVisible = true;
            _pageIndex = 0;
            _scrollOffset = 0;
            _activeMenu = -1;
            _hoverMenuItem = -1;
            _hoverButtonId = string.Empty;
            _lastAction = "无";
            _statusKind = StatusKind.Info;
            _statusText = "就绪：点击自绘输入框后直接键盘输入；所有自绘按钮需按住至少 300ms。";

            _caretTimer = new Timer { Interval = 530 };
            _caretTimer.Tick += CaretTimer_Tick;
            _animationTimer = new Timer { Interval = 16 };
            _animationTimer.Tick += AnimationTimer_Tick;

            RandomizeOffsets(false);
            AddEvent("自绘画布初始化 · 子控件 0 · AccessibleName 0");
            AddEvent("坐标随机化已启用 · 范围 ±30 px");
            AddEvent("按钮视觉防抖已启用 · 300 ms");
            _caretTimer.Start();
        }

        internal void HandleHostShortcut(Keys keyData)
        {
            if (keyData == Keys.F2)
            {
                ToggleTheme();
            }
            else if (keyData == Keys.F5)
            {
                RandomizeLayout();
            }
        }

        private void CaretTimer_Tick(object sender, EventArgs e)
        {
            if (_focusedField == InputField.None || !Focused)
            {
                return;
            }
            _caretVisible = !_caretVisible;
            Invalidate();
        }

        private void AnimationTimer_Tick(object sender, EventArgs e)
        {
            if (_pressedButton == null)
            {
                _animationTimer.Stop();
                return;
            }
            Invalidate(Inflate(_pressedButton.Bounds, 4));
        }

        private void EnsureLayout()
        {
            if (!_layoutDirty)
            {
                return;
            }
            if (Width < 320 || Height < 260)
            {
                return;
            }
            _layoutDirty = false;
            if (_pressedButton != null)
            {
                CancelPressedButton(false);
            }
            BuildLayout();
        }

        private void BuildLayout()
        {
            _buttons.Clear();

            int margin = 22;
            int headerHeight = 92;
            int gap = 16;
            int contentTop = headerHeight;
            int contentHeight = Math.Max(500, Height - contentTop - 18);
            int minimumBottom = 250;
            int topHeight = (int)(contentHeight * 0.56);
            topHeight = Math.Max(338, Math.Min(topHeight, contentHeight - minimumBottom - gap));
            if (topHeight < 250)
            {
                topHeight = Math.Max(230, contentHeight - minimumBottom - gap);
            }
            int bottomHeight = Math.Max(190, contentHeight - topHeight - gap);
            int columnWidth = Math.Max(360, (Width - margin * 2 - gap) / 2);

            _loginCard = new Rectangle(margin, contentTop, columnWidth, topHeight);
            _tableCard = new Rectangle(margin, contentTop + topHeight + gap, columnWidth, bottomHeight);
            _pageCard = new Rectangle(margin + columnWidth + gap, contentTop, columnWidth, topHeight);
            _statusCard = new Rectangle(margin + columnWidth + gap, contentTop + topHeight + gap, columnWidth, bottomHeight);

            BuildHeaderLayout();
            BuildLoginLayout();
            BuildTableLayout();
            BuildPageLayout();
            UpdateScrollThumbGeometry();
        }

        private void BuildHeaderLayout()
        {
            int menuStart = 424 + Offset("menu0").X;
            menuStart = Clamp(menuStart, 370, Math.Max(370, Width - 660));
            for (int i = 0; i < _menuBarRects.Length; i++)
            {
                _menuBarRects[i] = new Rectangle(menuStart + i * 76, 30, 70, 34);
            }

            int groupBase = Width - 22 - 150 - 10 - 128;
            int groupX = Clamp(groupBase + Offset("theme").X, 640, Math.Max(640, Width - 22 - 288));
            int themeY = Clamp(27 + Offset("theme").Y, 17, 41);
            int randomY = Clamp(27 + Offset("random").Y, 17, 41);

            AddButton(
                "theme",
                new Rectangle(groupX, themeY, 150, 38),
                _palette.Dark ? "切换到亮色  F2" : "切换到暗色  F2",
                false,
                ToggleTheme);

            AddButton(
                "random",
                new Rectangle(groupX + 160, randomY, 128, 38),
                "随机布局  F5",
                false,
                RandomizeLayout);
        }

        private void BuildLoginLayout()
        {
            Point vertical = Offset("inputsY");
            int minTop = _loginCard.Y + 58;
            int maxTop = Math.Max(minTop, _loginCard.Bottom - 248);
            int baseTop = _loginCard.Y + 76;
            int fieldsTop = Clamp(baseTop + vertical.Y, minTop, maxTop);

            int inputWidth = Math.Max(180, _loginCard.Width - 146);
            int inputMinX = _loginCard.X + 72;
            int inputMaxX = _loginCard.Right - 22 - inputWidth;
            if (inputMaxX < inputMinX)
            {
                inputMaxX = inputMinX;
            }

            _accountRect = new Rectangle(
                Clamp(_loginCard.X + 102 + Offset("account").X, inputMinX, inputMaxX),
                fieldsTop,
                inputWidth,
                34);

            _passwordRect = new Rectangle(
                Clamp(_loginCard.X + 102 + Offset("password").X, inputMinX, inputMaxX),
                fieldsTop + 44,
                inputWidth,
                34);

            _captchaInputRect = new Rectangle(
                Clamp(_loginCard.X + 102 + Offset("captcha").X, inputMinX, _loginCard.X + 170),
                fieldsTop + 88,
                122,
                34);

            int captchaVisualWidth = 118;
            int captchaVisualMinX = _loginCard.X + (int)(_loginCard.Width * 0.55);
            int captchaVisualMaxX = _loginCard.Right - 24 - captchaVisualWidth;
            if (captchaVisualMaxX < captchaVisualMinX)
            {
                captchaVisualMaxX = captchaVisualMinX;
            }
            _captchaVisualRect = new Rectangle(
                Clamp(_loginCard.Right - 22 - captchaVisualWidth + Offset("captchaVisual").X, captchaVisualMinX, captchaVisualMaxX),
                fieldsTop + 88 + Clamp(Offset("captchaVisual").Y, -8, 8),
                captchaVisualWidth,
                34);

            int loginX = Clamp(_loginCard.X + 102 + Offset("login").X, _loginCard.X + 72, _loginCard.X + 240);
            int loginY = Clamp(
                fieldsTop + 144 + Clamp(Offset("login").Y, -12, 12),
                fieldsTop + 134,
                _loginCard.Bottom - 102);
            AddButton("login", new Rectangle(loginX, loginY, 118, 40), "登 录", true, AttemptCustomLogin);
        }

        private void BuildTableLayout()
        {
            int tableTop = _tableCard.Y + 60;
            int tableBottom = _tableCard.Bottom - 14;
            int tableHeight = Math.Max(150, tableBottom - tableTop);
            int headerHeight = 32;
            int rowHeight = Math.Max(21, (tableHeight - headerHeight) / TableRowCount);

            _tableHeaderRect = new Rectangle(_tableCard.X + 18, tableTop, _tableCard.Width - 36, headerHeight);
            for (int i = 0; i < TableRowCount; i++)
            {
                _tableRowRects[i] = new Rectangle(
                    _tableHeaderRect.X,
                    _tableHeaderRect.Bottom + i * rowHeight,
                    _tableHeaderRect.Width,
                    rowHeight);
            }
        }

        private void BuildPageLayout()
        {
            int logHeight = Math.Max(110, _pageCard.Height - 152);
            _logViewport = new Rectangle(_pageCard.X + 18, _pageCard.Y + 60, _pageCard.Width - 36, logHeight);

            int scrollX = _logViewport.Right - 20;
            _scrollUpRect = new Rectangle(scrollX, _logViewport.Y + 6, 14, 14);
            _scrollDownRect = new Rectangle(scrollX, _logViewport.Bottom - 20, 14, 14);
            _scrollTrackRect = new Rectangle(
                scrollX,
                _scrollUpRect.Bottom + 2,
                14,
                Math.Max(16, _scrollDownRect.Top - _scrollUpRect.Bottom - 4));

            _totalLogLines = TestData.GetCanvasLog(_pageIndex).Length;
            _visibleLogLines = Math.Max(3, (_logViewport.Height - 34) / LogLineHeight);

            int buttonY = _pageCard.Bottom - 54;
            int prevX = Clamp(_pageCard.X + 18 + Offset("prev").X, _pageCard.X + 10, _pageCard.Right - 250);
            int nextX = Clamp(_pageCard.Right - 18 - 116 + Offset("next").X, _pageCard.X + 130, _pageCard.Right - 28 - 116);
            if (prevX + 100 > nextX - 8)
            {
                prevX = nextX - 108;
            }
            int prevY = Clamp(buttonY + Offset("prev").Y / 2, _pageCard.Bottom - 64, _pageCard.Bottom - 48);
            int nextY = Clamp(buttonY + Offset("next").Y / 2, _pageCard.Bottom - 64, _pageCard.Bottom - 48);

            AddButton("prev", new Rectangle(prevX, prevY, 100, 38), "上一页", false, delegate { ChangePage(-1); });
            AddButton("next", new Rectangle(nextX, nextY, 116, 38), "下一页", true, delegate { ChangePage(1); });
        }

        private void AddButton(string id, Rectangle bounds, string text, bool primary, Action action)
        {
            _buttons.Add(new CanvasButton(id, bounds, text, primary, action));
        }

        private CanvasButton FindButton(string id)
        {
            for (int i = 0; i < _buttons.Count; i++)
            {
                if (string.Equals(_buttons[i].Id, id, StringComparison.Ordinal))
                {
                    return _buttons[i];
                }
            }
            return null;
        }

        private void UpdateScrollThumbGeometry()
        {
            int maximumOffset = Math.Max(0, _totalLogLines - _visibleLogLines);
            _scrollOffset = Clamp(_scrollOffset, 0, maximumOffset);

            int trackHeight = _scrollTrackRect.Height;
            if (trackHeight <= 0 || _totalLogLines <= 0)
            {
                _scrollThumbRect = Rectangle.Empty;
                return;
            }

            int thumbHeight = _totalLogLines <= _visibleLogLines
                ? trackHeight
                : Math.Max(24, (int)(trackHeight * (double)_visibleLogLines / _totalLogLines));
            thumbHeight = Math.Min(trackHeight, thumbHeight);
            int thumbY = _scrollTrackRect.Y;
            if (maximumOffset > 0 && trackHeight > thumbHeight)
            {
                thumbY += (int)Math.Round((trackHeight - thumbHeight) * (double)_scrollOffset / maximumOffset);
            }

            _scrollThumbRect = new Rectangle(_scrollTrackRect.X, thumbY, _scrollTrackRect.Width, thumbHeight);
        }

        private void RandomizeOffsets(bool announce)
        {
            _jitter.Clear();
            string[] keys =
            {
                "menu0", "theme", "random",
                "account", "password", "captcha", "captchaVisual", "login",
                "prev", "next"
            };
            foreach (string key in keys)
            {
                _jitter[key] = new Point(RandomOffset(), RandomOffset());
            }
            _jitter["inputsY"] = new Point(0, RandomOffset());

            _layoutDirty = true;
            _hoverButtonId = string.Empty;
            CancelPressedButton(false);
            if (announce)
            {
                SetStatus("坐标已重新随机化（每个热点在 ±30 px 范围内偏移）。", StatusKind.Warning);
                AddEvent("layout.randomize · ±30 px");
            }
            Invalidate();
        }

        private int RandomOffset()
        {
            return _random.Next(-JitterRange, JitterRange + 1);
        }

        private Point Offset(string key)
        {
            Point value;
            return _jitter.TryGetValue(key, out value) ? value : Point.Empty;
        }

        private void RandomizeLayout()
        {
            RandomizeOffsets(true);
        }

        private void ToggleTheme()
        {
            _palette = _palette.Dark ? LightTheme : DarkTheme;
            BackColor = _palette.Background;
            _layoutDirty = true;
            SetStatus("主题已切换为" + (_palette.Dark ? "暗色" : "亮色") + "模式，图像匹配特征已改变。", StatusKind.Success);
            AddEvent("theme.toggle · " + (_palette.Dark ? "dark" : "light"));
            Invalidate();
        }

        private void ChangePage(int delta)
        {
            int count = TestData.CanvasPageCount;
            if (count <= 0)
            {
                return;
            }
            _pageIndex = (_pageIndex + delta + count) % count;
            _scrollOffset = 0;
            _layoutDirty = true;
            _activeMenu = -1;
            _hoverMenuItem = -1;
            SetStatus("已刷新画布内容：第 " + (_pageIndex + 1) + " / " + count + " 页（表格与日志同时更新）。", StatusKind.Info);
            AddEvent("paginator." + (delta < 0 ? "prev" : "next") + " -> page=" + (_pageIndex + 1));
            Invalidate();
        }

        private void AttemptCustomLogin()
        {
            if (_accountText.Length == 0 || _passwordText.Length == 0)
            {
                SetStatus("自绘登录失败：账号或密码为空。", StatusKind.Error);
                AddEvent("canvas.login · empty field");
                Invalidate();
                return;
            }
            if (!string.Equals(_captchaText, TestData.CaptchaText, StringComparison.OrdinalIgnoreCase))
            {
                SetStatus("自绘登录失败：验证码错误，图中固定验证码为 A8B9。", StatusKind.Error);
                AddEvent("canvas.login · captcha mismatch");
                Invalidate();
                return;
            }
            if (!string.Equals(_accountText, TestData.DemoAccount, StringComparison.Ordinal) ||
                !string.Equals(_passwordText, TestData.DemoPassword, StringComparison.Ordinal))
            {
                SetStatus("自绘登录失败：账号或密码错误，使用 admin / Admin@123。", StatusKind.Error);
                AddEvent("canvas.login · bad credentials");
                Invalidate();
                return;
            }

            SetStatus("自绘登录成功：admin（管理员）· 纯 GDI+ 输入链路。", StatusKind.Success);
            AddEvent("canvas.login · success");
            Invalidate();
        }

        private void ResetSession()
        {
            _accountText = string.Empty;
            _passwordText = string.Empty;
            _captchaText = string.Empty;
            _focusedField = InputField.None;
            _pageIndex = 0;
            _scrollOffset = 0;
            _layoutDirty = true;
            _activeMenu = -1;
            _hoverMenuItem = -1;
            SetStatus("会话已重置：输入、页码和滚动位置全部恢复。", StatusKind.Info);
            AddEvent("session.reset");
            Invalidate();
        }

        private void ClearEvents()
        {
            _events.Clear();
            AddEvent("事件日志已清空");
            SetStatus("事件日志已清空。", StatusKind.Info);
            Invalidate();
        }

        private void ExecuteMenuItem(int menuIndex, int itemIndex)
        {
            _activeMenu = -1;
            _hoverMenuItem = -1;

            if (menuIndex == 0 && itemIndex == 0)
            {
                ResetSession();
            }
            else if (menuIndex == 0 && itemIndex == 1)
            {
                RandomizeLayout();
            }
            else if (menuIndex == 0 && itemIndex == 2)
            {
                Form owner = FindForm();
                if (owner != null)
                {
                    owner.Close();
                }
            }
            else if (menuIndex == 1 && itemIndex == 0)
            {
                CopyAccount();
            }
            else if (menuIndex == 1 && itemIndex == 1)
            {
                PasteAccount();
            }
            else if (menuIndex == 1 && itemIndex == 2)
            {
                ClearEvents();
            }
            else if (menuIndex == 2 && itemIndex == 0)
            {
                SetStatus("F2 主题 · F5 随机布局 · Tab 切换输入 · Enter 登录 · Esc 清除焦点 · 滚轮滚动日志。", StatusKind.Info);
                AddEvent("help.shortcuts");
            }
            else if (menuIndex == 2 && itemIndex == 1)
            {
                SetStatus("纯 GDI+ 自绘靶场 · 无子控件 · 无 AccessibleName / AccessibleRole。", StatusKind.Info);
                AddEvent("help.about");
            }

            Invalidate();
        }

        private void CopyAccount()
        {
            try
            {
                if (_accountText.Length == 0)
                {
                    SetStatus("复制失败：账号输入框为空。", StatusKind.Warning);
                    return;
                }
                Clipboard.SetText(_accountText);
                SetStatus("已复制账号到剪贴板：" + _accountText, StatusKind.Success);
                AddEvent("clipboard.copy account");
            }
            catch (Exception ex)
            {
                SetStatus("复制失败：" + ex.Message, StatusKind.Error);
            }
        }

        private void PasteAccount()
        {
            if (!Clipboard.ContainsText())
            {
                SetStatus("粘贴失败：剪贴板中没有文本。", StatusKind.Warning);
                return;
            }

            string text = Clipboard.GetText().Replace("\r", string.Empty).Replace("\n", string.Empty);
            _accountText = Limit(text, 24);
            _focusedField = InputField.Account;
            _caretVisible = true;
            SetStatus("已从剪贴板粘贴到账号框。", StatusKind.Success);
            AddEvent("clipboard.paste account");
            Invalidate();
        }

        private void ScrollBy(int lines)
        {
            int maximumOffset = Math.Max(0, _totalLogLines - _visibleLogLines);
            int next = Clamp(_scrollOffset + lines, 0, maximumOffset);
            if (next == _scrollOffset)
            {
                return;
            }
            _scrollOffset = next;
            UpdateScrollThumbGeometry();
            Invalidate();
        }

        private void CycleFocus(bool backwards)
        {
            InputField next;
            if (backwards)
            {
                next = _focusedField == InputField.None
                    ? InputField.Captcha
                    : (InputField)((((int)_focusedField + 2) % 3) + 1);
            }
            else
            {
                next = _focusedField == InputField.None
                    ? InputField.Account
                    : (InputField)(((int)_focusedField % 3) + 1);
            }
            _focusedField = next;
            ResetCaret();
            SetStatus("输入焦点：" + GetFieldCaption(_focusedField) + "（Tab 继续切换）", StatusKind.Info);
            Invalidate();
        }

        private void ResetCaret()
        {
            _caretVisible = true;
        }

        private string GetFieldCaption(InputField field)
        {
            switch (field)
            {
                case InputField.Account:
                    return "账号";
                case InputField.Password:
                    return "密码";
                case InputField.Captcha:
                    return "验证码";
                default:
                    return "无";
            }
        }

        private string GetFieldText(InputField field)
        {
            switch (field)
            {
                case InputField.Account:
                    return _accountText;
                case InputField.Password:
                    return _passwordText;
                case InputField.Captcha:
                    return _captchaText;
                default:
                    return string.Empty;
            }
        }

        private void SetFieldText(InputField field, string value)
        {
            switch (field)
            {
                case InputField.Account:
                    _accountText = value;
                    break;
                case InputField.Password:
                    _passwordText = value;
                    break;
                case InputField.Captcha:
                    _captchaText = value;
                    break;
            }
        }

        private void AppendCharacter(char character)
        {
            if (_focusedField == InputField.None)
            {
                return;
            }

            if (_focusedField == InputField.Captcha)
            {
                if (!IsAsciiLetterOrDigit(character))
                {
                    return;
                }
                character = char.ToUpperInvariant(character);
            }

            string current = GetFieldText(_focusedField);
            int maximum = GetMaximumLength(_focusedField);
            if (current.Length >= maximum)
            {
                return;
            }

            SetFieldText(_focusedField, current + character);
            ResetCaret();
            Invalidate();
        }

        private void RemoveLastCharacter()
        {
            if (_focusedField == InputField.None)
            {
                return;
            }
            string current = GetFieldText(_focusedField);
            if (current.Length == 0)
            {
                return;
            }
            SetFieldText(_focusedField, current.Substring(0, current.Length - 1));
            ResetCaret();
            Invalidate();
        }

        private void PasteIntoFocusedField()
        {
            if (_focusedField == InputField.None || !Clipboard.ContainsText())
            {
                return;
            }

            string text = Clipboard.GetText().Replace("\r", string.Empty).Replace("\n", string.Empty);
            if (_focusedField == InputField.Captcha)
            {
                string filtered = string.Empty;
                foreach (char c in text)
                {
                    if (IsAsciiLetterOrDigit(c))
                    {
                        filtered += char.ToUpperInvariant(c);
                    }
                }
                text = filtered;
            }

            string current = GetFieldText(_focusedField);
            int maximum = GetMaximumLength(_focusedField);
            int room = Math.Max(0, maximum - current.Length);
            if (room > 0)
            {
                string addition = text.Length <= room ? text : text.Substring(0, room);
                SetFieldText(_focusedField, current + addition);
                SetStatus("已粘贴 " + addition.Length + " 个字符到" + GetFieldCaption(_focusedField) + "。", StatusKind.Info);
                AddEvent("keyboard.paste " + GetFieldCaption(_focusedField));
            }
            ResetCaret();
            Invalidate();
        }

        private static int GetMaximumLength(InputField field)
        {
            switch (field)
            {
                case InputField.Account:
                    return 24;
                case InputField.Password:
                    return 20;
                case InputField.Captcha:
                    return 4;
                default:
                    return 0;
            }
        }

        private static bool IsAsciiLetterOrDigit(char c)
        {
            return (c >= '0' && c <= '9') ||
                   (c >= 'a' && c <= 'z') ||
                   (c >= 'A' && c <= 'Z');
        }

        private static string Limit(string value, int maximum)
        {
            if (value == null)
            {
                return string.Empty;
            }
            return value.Length <= maximum ? value : value.Substring(0, maximum);
        }

        private void SetStatus(string text, StatusKind kind)
        {
            _statusText = text ?? string.Empty;
            _statusKind = kind;
            if (IsHandleCreated)
            {
                Invalidate();
            }
        }

        private void AddEvent(string message)
        {
            _events.Insert(0, string.Format("{0:HH:mm:ss}  {1}", DateTime.Now, message));
            while (_events.Count > 8)
            {
                _events.RemoveAt(_events.Count - 1);
            }
            _lastAction = message;
            if (IsHandleCreated)
            {
                Invalidate();
            }
        }

        private Color StatusColor(StatusKind kind)
        {
            switch (kind)
            {
                case StatusKind.Success:
                    return _palette.Success;
                case StatusKind.Warning:
                    return _palette.Warning;
                case StatusKind.Error:
                    return _palette.Danger;
                default:
                    return _palette.Accent;
            }
        }

        private void CancelPressedButton(bool invalidate)
        {
            _pressedButton = null;
            if (_animationTimer != null)
            {
                _animationTimer.Stop();
            }
            if (invalidate && IsHandleCreated)
            {
                Invalidate();
            }
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            EnsureLayout();
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.TextRenderingHint = TextRenderingHint.ClearTypeGridFit;
            g.Clear(_palette.Background);

            DrawBackdrop(g);
            DrawHeader(g);
            DrawLoginCard(g);
            DrawTableCard(g);
            DrawPageCard(g);
            DrawStatusCard(g);
            DrawButtons(g);
            DrawMenu(g);
        }

        private void DrawBackdrop(Graphics g)
        {
            int alpha = _palette.Dark ? 13 : 8;
            using (Pen pen = new Pen(Color.FromArgb(alpha, _palette.Accent), 1f))
            {
                for (int x = -Height; x < Width; x += 46)
                {
                    g.DrawLine(pen, x, 0, x + Height, Height);
                }
            }

            using (SolidBrush glow = new SolidBrush(Color.FromArgb(_palette.Dark ? 22 : 14, _palette.Accent2)))
            {
                g.FillEllipse(glow, Width - 420, -180, 680, 420);
                g.FillEllipse(glow, -220, Height - 260, 460, 300);
            }
        }

        private void DrawHeader(Graphics g)
        {
            using (SolidBrush accentBrush = new SolidBrush(_palette.Accent))
            {
                g.FillRectangle(accentBrush, 22, 20, 4, 42);
            }

            DrawText(g, "TAB 2 / CUSTOM CANVAS", _fontOverline, _palette.Accent,
                new Rectangle(36, 2, 330, 20), StringAlignment.Near, StringAlignment.Center);
            DrawTextAt(g, "地狱自绘靶场", _fontTitle, _palette.Text, 34, 20);
            DrawTextAt(g, "纯 GDI+ 绘制 · 0 个子控件 · 0 个 AccessibleName", _fontSubtitle, _palette.Muted, 36, 64);

            for (int i = 0; i < _menuBarRects.Length; i++)
            {
                Rectangle rect = _menuBarRects[i];
                bool active = _activeMenu == i;
                if (active)
                {
                    FillRounded(g, rect, 8, _palette.MenuHover);
                    StrokeRounded(g, rect, 8, _palette.Border, 1f);
                }

                DrawText(g, MenuLabels[i], _fontMenu, active ? _palette.Accent : _palette.Text,
                    rect, StringAlignment.Center, StringAlignment.Center);
            }

            using (Pen line = new Pen(_palette.HeaderLine, 1f))
            {
                g.DrawLine(line, 22, 90, Width - 22, 90);
            }
        }

        private void DrawLoginCard(Graphics g)
        {
            DrawCard(g, _loginCard, "01", "自绘登录框", "DrawRectangle + DrawString · 焦点 / 光标 / 退格");
            DrawFieldLabel(g, "账号", _accountRect, _focusedField == InputField.Account);
            DrawFieldLabel(g, "密码", _passwordRect, _focusedField == InputField.Password);
            DrawFieldLabel(g, "验证码", _captchaInputRect, _focusedField == InputField.Captcha);

            DrawInputBox(g, _accountRect, InputField.Account, "点击后输入账号");
            DrawInputBox(g, _passwordRect, InputField.Password, "点击后输入密码");
            DrawInputBox(g, _captchaInputRect, InputField.Captcha, "输入 A8B9");
            DrawCaptcha(g, _captchaVisualRect);

            DrawText(g, "固定验证码", _fontTiny, _palette.Muted,
                new Rectangle(_captchaVisualRect.X, _captchaVisualRect.Bottom + 1, 100, 18),
                StringAlignment.Near, StringAlignment.Center);

            CanvasButton login = FindButton("login");
            if (login != null)
            {
                DrawText(g, "按住 ≥300ms", _fontTiny, _palette.Warning,
                    new Rectangle(login.Bounds.Right + 8, login.Bounds.Y + 8, 160, 22),
                    StringAlignment.Near, StringAlignment.Center);

                if (login.Bounds.Bottom + 72 < _loginCard.Bottom - 56)
                {
                    int infoTop = login.Bounds.Bottom + 16;
                    DrawText(g, "键盘链路：OnKeyPress → 字符过滤 → 模型更新 → Invalidate", _fontTiny, _palette.Muted,
                        new Rectangle(_loginCard.X + 24, infoTop, _loginCard.Width - 48, 22),
                        StringAlignment.Near, StringAlignment.Center);
                    DrawText(g, "光标：530ms 闪烁 / Backspace 删除末字符 / Tab 切换三个字段", _fontTiny, _palette.Muted,
                        new Rectangle(_loginCard.X + 24, infoTop + 21, _loginCard.Width - 48, 22),
                        StringAlignment.Near, StringAlignment.Center);
                    DrawText(g,
                        "实时状态：焦点 " + GetFieldCaption(_focusedField) +
                        " · 账号 " + _accountText.Length +
                        " 字符 · 密码 " + _passwordText.Length +
                        " 字符 · 验证码 " + _captchaText.Length + " 字符",
                        _fontTiny, _palette.Accent,
                        new Rectangle(_loginCard.X + 24, infoTop + 42, _loginCard.Width - 48, 22),
                        StringAlignment.Near, StringAlignment.Center);
                }
            }

            DrawText(g, "演示账号 admin / Admin@123 · 验证码固定 A8B9", _fontTiny, _palette.Muted,
                new Rectangle(_loginCard.X + 22, _loginCard.Bottom - 56, _loginCard.Width - 44, 20),
                StringAlignment.Near, StringAlignment.Center);
            DrawText(g, _statusText, _fontSmall, StatusColor(_statusKind),
                new Rectangle(_loginCard.X + 22, _loginCard.Bottom - 34, _loginCard.Width - 44, 24),
                StringAlignment.Near, StringAlignment.Center);
        }

        private void DrawFieldLabel(Graphics g, string text, Rectangle field, bool focused)
        {
            DrawText(g, text, _fontBody, focused ? _palette.Accent : _palette.Muted,
                new Rectangle(_loginCard.X + 24, field.Y, 68, field.Height),
                StringAlignment.Near, StringAlignment.Center);
        }

        private void DrawInputBox(Graphics g, Rectangle rect, InputField field, string placeholder)
        {
            bool focused = _focusedField == field;
            FillRounded(g, rect, 8, _palette.Input);
            StrokeRounded(g, rect, 8, focused ? _palette.Accent : _palette.Border, focused ? 1.7f : 1f);

            string text = GetFieldText(field);
            string display = field == InputField.Password && text.Length > 0
                ? new string('*', text.Length)
                : text;

            if (display.Length == 0)
            {
                DrawText(g, placeholder, _fontSmall, _palette.Muted,
                    new Rectangle(rect.X + 10, rect.Y, rect.Width - 20, rect.Height),
                    StringAlignment.Near, StringAlignment.Center);
            }
            else
            {
                DrawText(g, display, _fontBody, _palette.Text,
                    new Rectangle(rect.X + 10, rect.Y, rect.Width - 20, rect.Height),
                    StringAlignment.Near, StringAlignment.Center);
            }

            if (focused && _caretVisible && Focused)
            {
                float measured = 0f;
                if (display.Length > 0)
                {
                    measured = g.MeasureString(display, _fontBody).Width;
                }
                float caretX = rect.X + 10f + measured;
                if (caretX > rect.Right - 10f)
                {
                    caretX = rect.Right - 10f;
                }
                using (Pen caret = new Pen(_palette.Accent, 1.6f))
                {
                    g.DrawLine(caret, caretX, rect.Y + 8, caretX, rect.Bottom - 8);
                }
            }
        }

        private void DrawCaptcha(Graphics g, Rectangle rect)
        {
            FillRounded(g, rect, 8, _palette.SurfaceAlt);
            GraphicsState outer = g.Save();
            g.SetClip(rect);

            Random noise = new Random(_captchaSeed);
            using (Pen noisePen = new Pen(Color.FromArgb(95, _palette.Muted), 1f))
            {
                for (int i = 0; i < 6; i++)
                {
                    int x1 = rect.Left + noise.Next(0, rect.Width);
                    int y1 = rect.Top + noise.Next(0, rect.Height);
                    int x2 = rect.Left + noise.Next(0, rect.Width);
                    int y2 = rect.Top + noise.Next(0, rect.Height);
                    g.DrawLine(noisePen, x1, y1, x2, y2);
                }
            }

            using (Pen arcPen = new Pen(Color.FromArgb(75, _palette.Accent2), 1f))
            {
                for (int i = 0; i < 3; i++)
                {
                    int x = rect.Left + noise.Next(4, Math.Max(5, rect.Width - 18));
                    int y = rect.Top + noise.Next(3, Math.Max(4, rect.Height - 14));
                    g.DrawEllipse(arcPen, x, y, 14, 8);
                }
            }

            string captcha = TestData.CaptchaText;
            float slot = rect.Width / (float)captcha.Length;
            for (int i = 0; i < captcha.Length; i++)
            {
                float angle = (float)(noise.NextDouble() * 22.0 - 11.0);
                using (SolidBrush brush = new SolidBrush(i % 2 == 0 ? _palette.Accent : _palette.Danger))
                using (StringFormat format = new StringFormat())
                {
                    format.Alignment = StringAlignment.Center;
                    format.LineAlignment = StringAlignment.Center;
                    GraphicsState inner = g.Save();
                    g.TranslateTransform(rect.Left + slot * i + slot / 2f, rect.Top + rect.Height / 2f + (i % 2 == 0 ? -1 : 2));
                    g.RotateTransform(angle);
                    g.DrawString(captcha[i].ToString(), _fontCaptcha, brush, new PointF(0f, 0f), format);
                    g.Restore(inner);
                }
            }

            g.Restore(outer);
            StrokeRounded(g, rect, 8, _palette.Border, 1f);
        }

        private void DrawTableCard(Graphics g)
        {
            DrawCard(g, _tableCard, "02", "自绘数据表格", "5 行 × 3 列 · 网格线由代码绘制 · 只能 OCR / 截图读取");

            IList<CanvasOrder> orders = TestData.GetCanvasOrders(_pageIndex);
            if (_tableHeaderRect.Width <= 0 || _tableHeaderRect.Height <= 0)
            {
                return;
            }

            int totalWidth = _tableHeaderRect.Width;
            int col0 = (int)(totalWidth * 0.46);
            int col1 = (int)(totalWidth * 0.28);
            int col2 = totalWidth - col0 - col1;

            using (LinearGradientBrush header = new LinearGradientBrush(
                _tableHeaderRect, _palette.Accent, _palette.Accent2, 0f))
            {
                g.FillRectangle(header, _tableHeaderRect);
            }

            Rectangle h0 = new Rectangle(_tableHeaderRect.X, _tableHeaderRect.Y, col0, _tableHeaderRect.Height);
            Rectangle h1 = new Rectangle(h0.Right, _tableHeaderRect.Y, col1, _tableHeaderRect.Height);
            Rectangle h2 = new Rectangle(h1.Right, _tableHeaderRect.Y, col2, _tableHeaderRect.Height);
            DrawText(g, "订单号", _fontTableHeader, _palette.AccentText, h0, StringAlignment.Near, StringAlignment.Center);
            DrawText(g, "状态", _fontTableHeader, _palette.AccentText, h1, StringAlignment.Near, StringAlignment.Center);
            DrawText(g, "金额", _fontTableHeader, _palette.AccentText, h2, StringAlignment.Far, StringAlignment.Center);

            for (int i = 0; i < TableRowCount; i++)
            {
                Rectangle row = _tableRowRects[i];
                Color background = i % 2 == 0 ? _palette.Surface : _palette.SurfaceAlt;
                using (SolidBrush brush = new SolidBrush(background))
                {
                    g.FillRectangle(brush, row);
                }

                CanvasOrder order = orders[i];
                Rectangle c0 = new Rectangle(row.X, row.Y, col0, row.Height);
                Rectangle c1 = new Rectangle(c0.Right, row.Y, col1, row.Height);
                Rectangle c2 = new Rectangle(c1.Right, row.Y, col2, row.Height);
                DrawText(g, order.OrderNo, _fontTable, _palette.Text, Inset(c0, 10, 0), StringAlignment.Near, StringAlignment.Center);
                DrawText(g, order.State, _fontTable, OrderStateColor(order.State), Inset(c1, 10, 0), StringAlignment.Near, StringAlignment.Center);
                DrawText(g, order.Amount, _fontTable, _palette.Text,
                    new Rectangle(c2.X, c2.Y, Math.Max(1, c2.Width - 12), c2.Height),
                    StringAlignment.Far, StringAlignment.Center);
            }

            using (Pen grid = new Pen(_palette.Grid, 1f))
            {
                int left = _tableHeaderRect.X;
                int top = _tableHeaderRect.Y;
                int right = _tableHeaderRect.Right;
                int bottom = _tableRowRects[TableRowCount - 1].Bottom;
                g.DrawLine(grid, left, _tableHeaderRect.Bottom, right, _tableHeaderRect.Bottom);
                g.DrawLine(grid, left + col0, top, left + col0, bottom);
                g.DrawLine(grid, left + col0 + col1, top, left + col0 + col1, bottom);
                for (int i = 0; i < TableRowCount; i++)
                {
                    g.DrawLine(grid, left, _tableRowRects[i].Bottom, right, _tableRowRects[i].Bottom);
                }
                g.DrawRectangle(grid, left, top, right - left - 1, bottom - top - 1);
            }

        }

        private Color OrderStateColor(string state)
        {
            if (state == "已完成" || state == "已支付" || state == "已发货" || state == "退款完成")
            {
                return _palette.Success;
            }
            if (state == "退款中" || state == "待发货" || state == "待支付")
            {
                return _palette.Warning;
            }
            if (state == "已关闭" || state == "已取消")
            {
                return _palette.Muted;
            }
            return _palette.Text;
        }

        private void DrawPageCard(Graphics g)
        {
            DrawCard(g, _pageCard, "03", "分页与自定义滚动条", "下一页刷新画布文字 · 滚轮 / 拖动滑块 · 无原生 ScrollBar");

            FillRounded(g, _logViewport, 9, _palette.Input);
            StrokeRounded(g, _logViewport, 9, _palette.Border, 1f);

            DrawText(g, "PAGE " + (_pageIndex + 1).ToString("00") + " / 03 · EVENT LOG", _fontOverline, _palette.Accent,
                new Rectangle(_logViewport.X + 10, _logViewport.Y + 5, _logViewport.Width - 52, 18),
                StringAlignment.Near, StringAlignment.Center);
            using (Pen separator = new Pen(_palette.Grid, 1f))
            {
                g.DrawLine(separator, _logViewport.X + 9, _logViewport.Y + 24, _logViewport.Right - 10, _logViewport.Y + 24);
            }

            string[] lines = TestData.GetCanvasLog(_pageIndex);
            Rectangle textRect = new Rectangle(
                _logViewport.X + 10,
                _logViewport.Y + 27,
                _logViewport.Width - 46,
                _logViewport.Height - 32);

            GraphicsState state = g.Save();
            g.SetClip(textRect);
            for (int i = 0; i < _visibleLogLines; i++)
            {
                int index = _scrollOffset + i;
                if (index >= lines.Length)
                {
                    break;
                }
                Color color = i == 0 ? _palette.Accent : _palette.Muted;
                DrawText(g, lines[index], _fontLog, color,
                    new Rectangle(textRect.X, textRect.Y + i * LogLineHeight, textRect.Width, LogLineHeight),
                    StringAlignment.Near, StringAlignment.Center);
            }
            g.Restore(state);

            DrawScrollbar(g);

            CanvasButton prev = FindButton("prev");
            CanvasButton next = FindButton("next");
            if (prev != null && next != null)
            {
                Rectangle pageLabel = new Rectangle(prev.Bounds.Right + 8, prev.Bounds.Y, Math.Max(80, next.Bounds.Left - prev.Bounds.Right - 16), prev.Bounds.Height);
                DrawText(g, "PAGE " + (_pageIndex + 1).ToString("00") + " / 03", _fontTableHeader, _palette.Text,
                    new Rectangle(pageLabel.X, pageLabel.Y + 1, pageLabel.Width, 20), StringAlignment.Center, StringAlignment.Center);
                DrawTextAt(g, _totalLogLines + " 行 · 滚动 " + _scrollOffset + "/" + Math.Max(0, _totalLogLines - _visibleLogLines),
                    _fontTiny, _palette.Muted, pageLabel.X + 8, pageLabel.Y + 22);
            }
        }

        private void DrawScrollbar(Graphics g)
        {
            using (SolidBrush trackBrush = new SolidBrush(_palette.SurfaceAlt))
            {
                g.FillRectangle(trackBrush, _scrollTrackRect);
            }
            using (Pen border = new Pen(_palette.Border, 1f))
            {
                g.DrawRectangle(border, _scrollTrackRect);
            }

            DrawScrollArrow(g, _scrollUpRect, true);
            DrawScrollArrow(g, _scrollDownRect, false);

            if (_scrollThumbRect.Height > 0)
            {
                Rectangle thumb = new Rectangle(
                    _scrollTrackRect.X + 2,
                    _scrollThumbRect.Y + 1,
                    Math.Max(4, _scrollTrackRect.Width - 4),
                    Math.Max(8, _scrollThumbRect.Height - 2));
                FillRounded(g, thumb, 4, _palette.Accent);
                using (SolidBrush grip = new SolidBrush(Color.FromArgb(170, _palette.AccentText)))
                {
                    int centerX = thumb.X + thumb.Width / 2;
                    int centerY = thumb.Y + thumb.Height / 2;
                    g.FillRectangle(grip, centerX - 3, centerY - 4, 6, 1);
                    g.FillRectangle(grip, centerX - 3, centerY, 6, 1);
                    g.FillRectangle(grip, centerX - 3, centerY + 4, 6, 1);
                }
            }
        }

        private void DrawScrollArrow(Graphics g, Rectangle rect, bool up)
        {
            using (SolidBrush brush = new SolidBrush(_palette.Muted))
            {
                Point[] points;
                if (up)
                {
                    points = new[]
                    {
                        new Point(rect.X + rect.Width / 2, rect.Y + 3),
                        new Point(rect.X + 3, rect.Bottom - 3),
                        new Point(rect.Right - 3, rect.Bottom - 3)
                    };
                }
                else
                {
                    points = new[]
                    {
                        new Point(rect.X + 3, rect.Y + 3),
                        new Point(rect.Right - 3, rect.Y + 3),
                        new Point(rect.X + rect.Width / 2, rect.Bottom - 3)
                    };
                }
                g.FillPolygon(brush, points);
            }
        }

        private void DrawStatusCard(Graphics g)
        {
            DrawCard(g, _statusCard, "04", "动态悬浮菜单", "Hover 文件 / 编辑 / 帮助 · 离开即消失 · 菜单项可点击");

            Color statusColor = StatusColor(_statusKind);
            Rectangle statusRect = new Rectangle(_statusCard.X + 16, _statusCard.Y + 58, _statusCard.Width - 32, 40);
            FillRounded(g, statusRect, 8, Color.FromArgb(22, statusColor));
            StrokeRounded(g, statusRect, 8, Color.FromArgb(80, statusColor), 1f);
            using (SolidBrush dot = new SolidBrush(statusColor))
            {
                g.FillEllipse(dot, statusRect.X + 12, statusRect.Y + 16, 8, 8);
            }
            DrawText(g, _statusText, _fontSmall, statusColor,
                new Rectangle(statusRect.X + 28, statusRect.Y, statusRect.Width - 40, statusRect.Height),
                StringAlignment.Near, StringAlignment.Center);

            string[] tips =
            {
                "• 顶部「文件 / 编辑 / 帮助」悬停打开浮动菜单",
                "• 自绘按钮需按住 ≥300ms，提前释放会被拦截",
                "• F2 主题 / F5 坐标随机化 / Tab 切换输入"
            };
            int tipsTop = statusRect.Bottom + 10;
            for (int i = 0; i < tips.Length; i++)
            {
                DrawTextAt(g, tips[i], _fontSmall, _palette.Muted,
                    _statusCard.X + 18, tipsTop + i * 23);
            }

            int eventTop = tipsTop + tips.Length * 23 + 8;
            DrawText(g, "RECENT EVENTS · " + _events.Count, _fontOverline, _palette.Accent,
                new Rectangle(_statusCard.X + 18, eventTop, _statusCard.Width - 36, 20),
                StringAlignment.Near, StringAlignment.Center);
            using (Pen line = new Pen(_palette.Grid, 1f))
            {
                g.DrawLine(line, _statusCard.X + 18, eventTop + 20, _statusCard.Right - 18, eventTop + 20);
            }

            int lineTop = eventTop + 27;
            int maximumLines = Math.Max(1, (_statusCard.Bottom - 8 - lineTop) / 23);
            for (int i = 0; i < _events.Count && i < maximumLines; i++)
            {
                DrawTextAt(g, _events[i], _fontTiny, i == 0 ? _palette.Text : _palette.Muted,
                    _statusCard.X + 18, lineTop + i * 23);
            }
        }

        private void DrawButtons(Graphics g)
        {
            for (int i = 0; i < _buttons.Count; i++)
            {
                CanvasButton button = _buttons[i];
                bool hovered = string.Equals(_hoverButtonId, button.Id, StringComparison.Ordinal);
                bool pressed = _pressedButton != null && ReferenceEquals(_pressedButton, button);
                float progress = 0f;
                if (pressed)
                {
                    progress = (float)Math.Min(1.0, (DateTime.UtcNow - _pressStartUtc).TotalMilliseconds / AntiBounceMs);
                }

                Color start;
                Color end;
                Color textColor;
                Color borderColor;

                if (button.Primary)
                {
                    start = _palette.Accent;
                    end = _palette.Accent2;
                    textColor = _palette.AccentText;
                    borderColor = Color.Transparent;
                    if (hovered && !pressed)
                    {
                        start = Blend(start, Color.White, 0.10f);
                        end = Blend(end, Color.White, 0.06f);
                    }
                    if (pressed)
                    {
                        Color pressedTint = Blend(_palette.Accent, Color.Black, 0.28f);
                        start = Blend(start, pressedTint, progress);
                        end = Blend(end, pressedTint, progress);
                    }
                }
                else
                {
                    start = _palette.SurfaceAlt;
                    end = _palette.Input;
                    textColor = _palette.Text;
                    borderColor = hovered ? _palette.Accent : _palette.Border;
                    if (hovered && !pressed)
                    {
                        start = Blend(start, _palette.Accent, 0.09f);
                        end = Blend(end, _palette.Accent, 0.05f);
                    }
                    if (pressed)
                    {
                        start = Blend(start, _palette.Accent, 0.18f * progress);
                        end = Blend(end, _palette.Accent, 0.12f * progress);
                    }
                }

                Rectangle rect = button.Bounds;
                using (GraphicsPath path = RoundedPath(rect, 9))
                using (LinearGradientBrush brush = new LinearGradientBrush(rect, start, end, 0f))
                {
                    g.FillPath(brush, path);
                    if (borderColor.A > 0)
                    {
                        using (Pen border = new Pen(borderColor, hovered ? 1.6f : 1f))
                        {
                            g.DrawPath(border, path);
                        }
                    }
                }

                if (pressed)
                {
                    int progressWidth = (int)Math.Round((rect.Width - 8) * progress);
                    if (progressWidth > 0)
                    {
                        Rectangle bar = new Rectangle(rect.X + 4, rect.Bottom - 5, progressWidth, 2);
                        using (SolidBrush barBrush = new SolidBrush(Color.FromArgb(210, _palette.AccentText)))
                        {
                            g.FillRectangle(barBrush, bar);
                        }
                    }
                }

                DrawText(g, button.Text, _fontButton, textColor, rect,
                    StringAlignment.Center, StringAlignment.Center);
            }
        }

        private void DrawMenu(Graphics g)
        {
            if (_activeMenu < 0 || _activeMenu >= MenuItems.Length)
            {
                return;
            }

            Rectangle drop = GetMenuDropRect(_activeMenu);
            FillRounded(g, new Rectangle(drop.X + 2, drop.Y + 4, drop.Width, drop.Height), 10, _palette.Shadow);
            FillRounded(g, drop, 10, _palette.MenuSurface);
            StrokeRounded(g, drop, 10, _palette.Border, 1f);

            string[] items = MenuItems[_activeMenu];
            for (int i = 0; i < items.Length; i++)
            {
                Rectangle item = GetMenuItemRect(drop, i);
                if (_hoverMenuItem == i)
                {
                    FillRounded(g, Inflate(item, -4, -1), 7, _palette.MenuHover);
                }
                Color color = (_activeMenu == 0 && i == 2) ? _palette.Danger : _palette.Text;
                DrawText(g, items[i], _fontMenu, color,
                    new Rectangle(item.X + 12, item.Y, item.Width - 24, item.Height),
                    StringAlignment.Near, StringAlignment.Center);
            }
        }

        private Rectangle GetMenuDropRect(int menuIndex)
        {
            if (menuIndex < 0 || menuIndex >= _menuBarRects.Length)
            {
                return Rectangle.Empty;
            }
            Rectangle label = _menuBarRects[menuIndex];
            int width = 220;
            int height = MenuItems[menuIndex].Length * 34 + 12;
            int x = Clamp(label.X - 10, 12, Math.Max(12, Width - width - 12));
            int y = label.Bottom + 6;
            return new Rectangle(x, y, width, height);
        }

        private Rectangle GetMenuItemRect(Rectangle drop, int itemIndex)
        {
            return new Rectangle(drop.X + 6, drop.Y + 6 + itemIndex * 34, drop.Width - 12, 34);
        }

        private void DrawCard(Graphics g, Rectangle rect, string number, string title, string subtitle)
        {
            FillRounded(g, new Rectangle(rect.X + 2, rect.Y + 4, rect.Width, rect.Height), 13, _palette.Shadow);
            FillRounded(g, rect, 13, _palette.Surface);
            StrokeRounded(g, rect, 13, _palette.Border, 1f);

            Rectangle badge = new Rectangle(rect.X + 16, rect.Y + 15, 38, 22);
            FillRounded(g, badge, 7, _palette.Accent);
            DrawText(g, number, _fontOverline, _palette.AccentText, badge,
                StringAlignment.Center, StringAlignment.Center);

            DrawText(g, title, _fontCardTitle, _palette.Text,
                new Rectangle(rect.X + 64, rect.Y + 6, rect.Width - 126, 30),
                StringAlignment.Near, StringAlignment.Center);
            DrawText(g, subtitle, _fontCardHint, _palette.Muted,
                new Rectangle(rect.X + 65, rect.Y + 35, rect.Width - 108, 20),
                StringAlignment.Near, StringAlignment.Center);

            using (Pen line = new Pen(_palette.Grid, 1f))
            {
                g.DrawLine(line, rect.X + 16, rect.Y + 55, rect.Right - 16, rect.Y + 55);
            }
        }

        private void DrawText(Graphics g, string text, Font font, Color color, Rectangle bounds, StringAlignment alignment, StringAlignment lineAlignment)
        {
            if (bounds.Width <= 0 || bounds.Height <= 0 || string.IsNullOrEmpty(text))
            {
                return;
            }

            using (SolidBrush brush = new SolidBrush(color))
            using (StringFormat format = new StringFormat(StringFormat.GenericTypographic))
            {
                format.Alignment = alignment;
                format.LineAlignment = lineAlignment;
                format.Trimming = StringTrimming.EllipsisCharacter;
                format.FormatFlags |= StringFormatFlags.NoWrap;
                format.FormatFlags |= StringFormatFlags.NoClip;
                g.DrawString(text, font, brush, new RectangleF(bounds.X, bounds.Y, bounds.Width, bounds.Height), format);
            }
        }

        private void DrawTextAt(Graphics g, string text, Font font, Color color, int x, int y)
        {
            if (string.IsNullOrEmpty(text))
            {
                return;
            }

            using (SolidBrush brush = new SolidBrush(color))
            using (StringFormat format = new StringFormat(StringFormat.GenericTypographic))
            {
                format.FormatFlags |= StringFormatFlags.NoClip;
                g.DrawString(text, font, brush, new PointF(x, y), format);
            }
        }

        private static Rectangle Inset(Rectangle rect, int horizontal, int vertical)
        {
            return new Rectangle(rect.X + horizontal, rect.Y + vertical, Math.Max(1, rect.Width - horizontal), Math.Max(1, rect.Height - vertical));
        }

        private static Rectangle Inflate(Rectangle rect, int horizontal, int vertical)
        {
            return new Rectangle(rect.X - horizontal, rect.Y - vertical, rect.Width + horizontal * 2, rect.Height + vertical * 2);
        }

        private static Color Blend(Color from, Color to, float amount)
        {
            amount = Math.Max(0f, Math.Min(1f, amount));
            return Color.FromArgb(
                (int)(from.A + (to.A - from.A) * amount),
                (int)(from.R + (to.R - from.R) * amount),
                (int)(from.G + (to.G - from.G) * amount),
                (int)(from.B + (to.B - from.B) * amount));
        }

        private static void FillRounded(Graphics g, Rectangle rect, int radius, Color color)
        {
            if (rect.Width <= 0 || rect.Height <= 0)
            {
                return;
            }
            using (GraphicsPath path = RoundedPath(rect, radius))
            using (SolidBrush brush = new SolidBrush(color))
            {
                g.FillPath(brush, path);
            }
        }

        private static void StrokeRounded(Graphics g, Rectangle rect, int radius, Color color, float width)
        {
            if (rect.Width <= 0 || rect.Height <= 0)
            {
                return;
            }
            using (GraphicsPath path = RoundedPath(rect, radius))
            using (Pen pen = new Pen(color, width))
            {
                g.DrawPath(pen, path);
            }
        }

        private static GraphicsPath RoundedPath(Rectangle rect, int radius)
        {
            GraphicsPath path = new GraphicsPath();
            int diameter = Math.Max(2, Math.Min(radius * 2, Math.Min(rect.Width, rect.Height)));
            Rectangle arc = new Rectangle(rect.X, rect.Y, diameter, diameter);
            path.AddArc(arc, 180, 90);
            arc.X = rect.Right - diameter;
            path.AddArc(arc, 270, 90);
            arc.Y = rect.Bottom - diameter;
            path.AddArc(arc, 0, 90);
            arc.X = rect.X;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }

        private static int Clamp(int value, int minimum, int maximum)
        {
            if (maximum < minimum)
            {
                return minimum;
            }
            return Math.Max(minimum, Math.Min(maximum, value));
        }

        private static Rectangle Inflate(Rectangle rect, int amount)
        {
            return new Rectangle(rect.X - amount, rect.Y - amount, rect.Width + amount * 2, rect.Height + amount * 2);
        }

        private CanvasButton HitButton(Point point)
        {
            for (int i = _buttons.Count - 1; i >= 0; i--)
            {
                if (_buttons[i].Bounds.Contains(point))
                {
                    return _buttons[i];
                }
            }
            return null;
        }

        private int HitMenuBar(Point point)
        {
            for (int i = 0; i < _menuBarRects.Length; i++)
            {
                if (_menuBarRects[i].Contains(point))
                {
                    return i;
                }
            }
            return -1;
        }

        private int HitMenuItem(Point point)
        {
            if (_activeMenu < 0)
            {
                return -1;
            }
            Rectangle drop = GetMenuDropRect(_activeMenu);
            if (!drop.Contains(point))
            {
                return -1;
            }
            string[] items = MenuItems[_activeMenu];
            for (int i = 0; i < items.Length; i++)
            {
                if (GetMenuItemRect(drop, i).Contains(point))
                {
                    return i;
                }
            }
            return -1;
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            EnsureLayout();
            Focus();

            if (e.Button != MouseButtons.Left)
            {
                return;
            }

            int menuBar = HitMenuBar(e.Location);
            if (menuBar >= 0)
            {
                _activeMenu = menuBar;
                _hoverMenuItem = -1;
                Invalidate();
                return;
            }

            if (_activeMenu >= 0)
            {
                Rectangle drop = GetMenuDropRect(_activeMenu);
                if (drop.Contains(e.Location))
                {
                    int item = HitMenuItem(e.Location);
                    if (item >= 0)
                    {
                        ExecuteMenuItem(_activeMenu, item);
                    }
                    return;
                }
                _activeMenu = -1;
                _hoverMenuItem = -1;
            }

            CanvasButton button = HitButton(e.Location);
            if (button != null)
            {
                _activeMenu = -1;
                _hoverMenuItem = -1;
                _pressedButton = button;
                _pressStartUtc = DateTime.UtcNow;
                _animationTimer.Start();
                Capture = true;
                SetStatus("已按下“" + button.Text.Trim() + "”，请保持至少 300ms 后释放。", StatusKind.Info);
                Invalidate();
                return;
            }

            if (_scrollUpRect.Contains(e.Location))
            {
                ScrollBy(-1);
                return;
            }
            if (_scrollDownRect.Contains(e.Location))
            {
                ScrollBy(1);
                return;
            }
            if (_scrollThumbRect.Contains(e.Location) && _scrollThumbRect.Height > 0)
            {
                _draggingThumb = true;
                _dragThumbOffset = e.Y - _scrollThumbRect.Y;
                Capture = true;
                Cursor = Cursors.SizeNS;
                return;
            }
            if (_scrollTrackRect.Contains(e.Location))
            {
                ScrollBy(e.Y < _scrollThumbRect.Y ? -(_visibleLogLines - 1) : (_visibleLogLines - 1));
                return;
            }

            if (_accountRect.Contains(e.Location))
            {
                _focusedField = InputField.Account;
                ResetCaret();
                SetStatus("输入焦点：账号（支持退格、Ctrl+V 与 Tab 切换）", StatusKind.Info);
                Invalidate();
                return;
            }
            if (_passwordRect.Contains(e.Location))
            {
                _focusedField = InputField.Password;
                ResetCaret();
                SetStatus("输入焦点：密码（输入内容以 * 遮罩）", StatusKind.Info);
                Invalidate();
                return;
            }
            if (_captchaInputRect.Contains(e.Location))
            {
                _focusedField = InputField.Captcha;
                ResetCaret();
                SetStatus("输入焦点：验证码（固定 A8B9，最多 4 位）", StatusKind.Info);
                Invalidate();
                return;
            }

            _focusedField = InputField.None;
            Invalidate();
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);

            if (e.Button != MouseButtons.Left)
            {
                return;
            }

            if (_draggingThumb)
            {
                _draggingThumb = false;
                Capture = false;
                Cursor = Cursors.Default;
                Invalidate();
                return;
            }

            if (_pressedButton == null)
            {
                return;
            }

            CanvasButton button = _pressedButton;
            _pressedButton = null;
            _animationTimer.Stop();
            Capture = false;

            double elapsed = (DateTime.UtcNow - _pressStartUtc).TotalMilliseconds;
            bool inside = button.Bounds.Contains(e.Location);

            if (inside && elapsed >= AntiBounceMs)
            {
                SetStatus("已触发“" + button.Text.Trim() + "”（按住 " + (int)elapsed + "ms）。", StatusKind.Success);
                Invalidate();
                button.Action();
            }
            else if (inside)
            {
                SetStatus("视觉防抖拦截：只按住了 " + (int)elapsed + "ms，少于 300ms，操作已取消。", StatusKind.Error);
                AddEvent("anti-bounce reject · " + (int)elapsed + "ms");
                Invalidate();
            }
            else
            {
                SetStatus("按钮在按下后移出，操作已取消。", StatusKind.Warning);
                Invalidate();
            }
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            EnsureLayout();

            if (_draggingThumb)
            {
                int maximumOffset = Math.Max(0, _totalLogLines - _visibleLogLines);
                int available = Math.Max(0, _scrollTrackRect.Height - _scrollThumbRect.Height);
                if (available > 0 && maximumOffset > 0)
                {
                    int localTop = Clamp(e.Y - _dragThumbOffset - _scrollTrackRect.Y, 0, available);
                    _scrollOffset = (int)Math.Round((double)localTop * maximumOffset / available);
                    UpdateScrollThumbGeometry();
                    Invalidate();
                }
                Cursor = Cursors.SizeNS;
                return;
            }

            CanvasButton button = HitButton(e.Location);
            string hoverId = button == null ? string.Empty : button.Id;
            bool changed = !string.Equals(hoverId, _hoverButtonId, StringComparison.Ordinal);
            _hoverButtonId = hoverId;

            int menuBar = HitMenuBar(e.Location);
            if (menuBar >= 0)
            {
                if (_activeMenu != menuBar)
                {
                    _activeMenu = menuBar;
                    changed = true;
                }
                if (_hoverMenuItem != -1)
                {
                    _hoverMenuItem = -1;
                    changed = true;
                }
            }
            else if (_activeMenu >= 0)
            {
                Rectangle drop = GetMenuDropRect(_activeMenu);
                Rectangle label = _menuBarRects[_activeMenu];
                Rectangle corridor = new Rectangle(
                    drop.X,
                    label.Bottom,
                    drop.Width,
                    Math.Max(0, drop.Top - label.Bottom));
                if (drop.Contains(e.Location) || corridor.Contains(e.Location))
                {
                    int item = drop.Contains(e.Location) ? HitMenuItem(e.Location) : -1;
                    if (item != _hoverMenuItem)
                    {
                        _hoverMenuItem = item;
                        changed = true;
                    }
                }
                else
                {
                    _activeMenu = -1;
                    _hoverMenuItem = -1;
                    changed = true;
                }
            }

            bool overInput = _accountRect.Contains(e.Location) ||
                             _passwordRect.Contains(e.Location) ||
                             _captchaInputRect.Contains(e.Location);
            bool overScrollbar = _scrollUpRect.Contains(e.Location) ||
                                 _scrollDownRect.Contains(e.Location) ||
                                 _scrollTrackRect.Contains(e.Location) ||
                                 _scrollThumbRect.Contains(e.Location);

            if (menuBar >= 0 || _activeMenu >= 0 || button != null || overScrollbar)
            {
                Cursor = Cursors.Hand;
            }
            else if (overInput)
            {
                Cursor = Cursors.IBeam;
            }
            else
            {
                Cursor = Cursors.Default;
            }

            if (changed)
            {
                Invalidate();
            }
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            base.OnMouseLeave(e);
            if (_draggingThumb)
            {
                return;
            }
            _activeMenu = -1;
            _hoverMenuItem = -1;
            _hoverButtonId = string.Empty;
            Cursor = Cursors.Default;
            Invalidate();
        }

        protected override void OnMouseWheel(MouseEventArgs e)
        {
            base.OnMouseWheel(e);
            EnsureLayout();
            if (_logViewport.Contains(e.Location) || _scrollTrackRect.Contains(e.Location))
            {
                ScrollBy(e.Delta > 0 ? -2 : 2);
            }
        }

        protected override bool IsInputKey(Keys keyData)
        {
            Keys key = keyData & Keys.KeyCode;
            if (key == Keys.Tab || key == Keys.Enter || key == Keys.Back || key == Keys.Escape)
            {
                return true;
            }
            return base.IsInputKey(keyData);
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);

            if (e.KeyCode == Keys.F2)
            {
                ToggleTheme();
                e.SuppressKeyPress = true;
                return;
            }
            if (e.KeyCode == Keys.F5)
            {
                RandomizeLayout();
                e.SuppressKeyPress = true;
                return;
            }
            if (e.Control && e.KeyCode == Keys.V)
            {
                PasteIntoFocusedField();
                e.SuppressKeyPress = true;
                return;
            }
            if (e.KeyCode == Keys.Back)
            {
                RemoveLastCharacter();
                e.SuppressKeyPress = true;
                return;
            }
            if (e.KeyCode == Keys.Tab)
            {
                CycleFocus(e.Shift);
                e.SuppressKeyPress = true;
                return;
            }
            if (e.KeyCode == Keys.Enter)
            {
                if (_focusedField == InputField.None)
                {
                    _focusedField = InputField.Account;
                    ResetCaret();
                    SetStatus("输入焦点：账号（按 Enter 登录）", StatusKind.Info);
                    Invalidate();
                }
                else
                {
                    AttemptCustomLogin();
                }
                e.SuppressKeyPress = true;
                return;
            }
            if (e.KeyCode == Keys.Escape)
            {
                _focusedField = InputField.None;
                _activeMenu = -1;
                _hoverMenuItem = -1;
                SetStatus("已清除输入焦点与悬浮菜单。", StatusKind.Info);
                Invalidate();
                e.SuppressKeyPress = true;
            }
        }

        protected override void OnKeyPress(KeyPressEventArgs e)
        {
            base.OnKeyPress(e);

            if (_focusedField == InputField.None)
            {
                return;
            }

            if (char.IsControl(e.KeyChar))
            {
                e.Handled = true;
                return;
            }

            if ((Control.ModifierKeys & (Keys.Control | Keys.Alt)) != Keys.None)
            {
                e.Handled = true;
                return;
            }

            AppendCharacter(e.KeyChar);
            e.Handled = true;
        }

        protected override void OnGotFocus(EventArgs e)
        {
            base.OnGotFocus(e);
            Invalidate();
        }

        protected override void OnLostFocus(EventArgs e)
        {
            base.OnLostFocus(e);
            _caretVisible = false;
            if (_pressedButton != null)
            {
                CancelPressedButton(false);
            }
            Capture = false;
            _draggingThumb = false;
            Invalidate();
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            _layoutDirty = true;
            _activeMenu = -1;
            _hoverMenuItem = -1;
            CancelPressedButton(false);
            Capture = false;
            _draggingThumb = false;
            Invalidate();
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _caretTimer.Stop();
                _caretTimer.Dispose();
                _animationTimer.Stop();
                _animationTimer.Dispose();

                _fontOverline.Dispose();
                _fontTitle.Dispose();
                _fontSubtitle.Dispose();
                _fontCardTitle.Dispose();
                _fontCardHint.Dispose();
                _fontBody.Dispose();
                _fontSmall.Dispose();
                _fontTiny.Dispose();
                _fontButton.Dispose();
                _fontTableHeader.Dispose();
                _fontTable.Dispose();
                _fontLog.Dispose();
                _fontCaptcha.Dispose();
                _fontMenu.Dispose();
            }
            base.Dispose(disposing);
        }

        private enum InputField
        {
            None,
            Account,
            Password,
            Captcha
        }

        private enum StatusKind
        {
            Info,
            Success,
            Warning,
            Error
        }

        private sealed class CanvasButton
        {
            public CanvasButton(string id, Rectangle bounds, string text, bool primary, Action action)
            {
                Id = id;
                Bounds = bounds;
                Text = text;
                Primary = primary;
                Action = action;
            }

            public string Id { get; private set; }
            public Rectangle Bounds { get; private set; }
            public string Text { get; private set; }
            public bool Primary { get; private set; }
            public Action Action { get; private set; }
        }

        private sealed class CanvasPalette
        {
            public bool Dark;
            public Color Background;
            public Color BackgroundAlt;
            public Color Surface;
            public Color SurfaceAlt;
            public Color Border;
            public Color Text;
            public Color Muted;
            public Color Accent;
            public Color Accent2;
            public Color AccentText;
            public Color Input;
            public Color Grid;
            public Color Success;
            public Color Warning;
            public Color Danger;
            public Color MenuSurface;
            public Color MenuHover;
            public Color Shadow;
            public Color HeaderLine;
        }
    }
}
