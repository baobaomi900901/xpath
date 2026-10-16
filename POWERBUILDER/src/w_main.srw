$PBExportHeader$w_main.srw
forward
global type w_main from window
end type
type tab_main from tab within w_main
end type
type tabpage_form from u_form within tab_main
end type
type tabpage_table from u_table within tab_main
end type
type tabpage_drag from u_drag within tab_main
end type
type st_menu from statictext within w_main
end type
end forward

global type w_main from window
integer x = 80
integer y = 40
integer width = 4900
integer height = 3100
boolean titlebar = true
string title = "PowerBuilder 靶场 - 原生控件 / DataWindow"
string menuname = "m_main"
boolean controlmenu = true
boolean minbox = true
boolean maxbox = true
boolean resizable = true
windowtype windowtype = main!
long backcolor = 67108864
string accessiblename = "PowerBuilder 靶场"
tab_main tab_main
st_menu st_menu
end type
global w_main w_main

forward prototypes
public subroutine of_menu (string as_action)
public subroutine of_fit_screen ()
end prototypes

public subroutine of_menu (string as_action);
st_menu.Text = "菜单状态：" + as_action
st_menu.AccessibleName = st_menu.Text
end subroutine

public subroutine of_fit_screen ();
environment lenv
double ld_scale
long ll_width, ll_height
GetEnvironment(lenv)
ll_width = PixelsToUnits(Min(1180, lenv.ScreenWidth - 80), XPixelsToUnits!)
ll_height = PixelsToUnits(Min(800, lenv.ScreenHeight - 100), YPixelsToUnits!)
ld_scale = Min(1, Min(Double(ll_width) / 4900, Double(ll_height) / 3100)) * 0.99
this.Resize(Long(4900 * ld_scale), Long(3100 * ld_scale))
// Title bar, menus and borders keep their system dimensions at high DPI.
// Fit the children to the actual client area after resizing the outer window.
ld_scale = Min(ld_scale, Min(Double(this.WorkSpaceWidth()) / 4850, Double(this.WorkSpaceHeight()) / 3000)) * 0.99
f_scale_controls(this.Control, ld_scale)
f_scale_controls(tab_main.tabpage_form.Control, ld_scale)
f_scale_controls(tab_main.tabpage_table.Control, ld_scale)
f_scale_controls(tab_main.tabpage_drag.Control, ld_scale)
tab_main.tabpage_form.Resize(Long(4700 * ld_scale), Long(2650 * ld_scale))
tab_main.tabpage_table.Resize(Long(4700 * ld_scale), Long(2650 * ld_scale))
tab_main.tabpage_drag.Resize(Long(4700 * ld_scale), Long(2650 * ld_scale))
tab_main.tabpage_table.of_scale_data(ld_scale)
this.Move(PixelsToUnits((lenv.ScreenWidth - UnitsToPixels(this.Width, XUnitsToPixels!)) / 2, XPixelsToUnits!), PixelsToUnits((lenv.ScreenHeight - UnitsToPixels(this.Height, YUnitsToPixels!)) / 2, YPixelsToUnits!))
end subroutine

on w_main.create
if this.MenuName = "m_main" then this.MenuID = create m_main
this.tab_main = create tab_main
this.st_menu = create st_menu
this.Control[] = {this.tab_main, this.st_menu}
end on

on w_main.destroy
destroy(this.tab_main)
destroy(this.st_menu)
end on

event open;
tab_main.tabpage_form.of_reset()
tab_main.tabpage_table.of_initialize()
of_fit_screen()
tab_main.tabpage_drag.uo_arena.of_reset()
tab_main.tabpage_drag.of_update()
tab_main.SelectTab(1)
end event

type tab_main from tab within w_main
integer x = 50
integer y = 40
integer width = 4750
integer height = 2800
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer selectedtab = 1
string accessiblename = "靶场页签"
tabpage_form tabpage_form
tabpage_table tabpage_table
tabpage_drag tabpage_drag
end type

on tab_main.create
this.tabpage_form = create tabpage_form
this.tabpage_table = create tabpage_table
this.tabpage_drag = create tabpage_drag
this.Control[] = {this.tabpage_form, this.tabpage_table, this.tabpage_drag}
end on

on tab_main.destroy
destroy(this.tabpage_form)
destroy(this.tabpage_table)
destroy(this.tabpage_drag)
end on

type tabpage_form from u_form within tab_main
string text = "表单控件"
end type

type tabpage_table from u_table within tab_main
string text = "表格数据"
end type

type tabpage_drag from u_drag within tab_main
string text = "拖拽测试"
end type

type st_menu from statictext within w_main
integer x = 100
integer y = 2880
integer width = 4600
integer height = 100
integer textsize = -9
string facename = "Microsoft YaHei UI"
string text = "菜单状态：尚未操作"
string accessiblename = "菜单状态"
end type
