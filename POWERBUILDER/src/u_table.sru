$PBExportHeader$u_table.sru
forward
global type u_table from userobject
end type
type st_title from statictext within u_table
end type
type dw_employees from datawindow within u_table
end type
type st_page from statictext within u_table
end type
type cb_first from commandbutton within u_table
end type
type cb_previous from commandbutton within u_table
end type
type cb_page1 from commandbutton within u_table
end type
type cb_page2 from commandbutton within u_table
end type
type cb_page3 from commandbutton within u_table
end type
type cb_page4 from commandbutton within u_table
end type
type cb_page5 from commandbutton within u_table
end type
type cb_next from commandbutton within u_table
end type
type cb_last from commandbutton within u_table
end type
end forward

global type u_table from userobject
integer width = 4700
integer height = 2650
string text = "表格数据"
string accessiblename = "表格数据"
st_title st_title
dw_employees dw_employees
st_page st_page
cb_first cb_first
cb_previous cb_previous
cb_page1 cb_page1
cb_page2 cb_page2
cb_page3 cb_page3
cb_page4 cb_page4
cb_page5 cb_page5
cb_next cb_next
cb_last cb_last
end type
global u_table u_table

type variables
long il_page = 1
boolean ib_ready = false
string is_error
end variables

forward prototypes
public function boolean of_initialize ()
public subroutine of_showpage (long al_page)
public subroutine of_scale_data (double ad_scale)
end prototypes

public function boolean of_initialize ();
string ls_error, ls_syntax
ls_syntax = "release 25; datawindow(units=0 color=1073741824 processing=1) header(height=120 color=~"536870912~") summary(height=0 color=~"536870912~") footer(height=0 color=~"536870912~") detail(height=100 color=~"536870912~") table(column=(type=long updatewhereclause=yes name=employee_id dbname=~"employee_id~") column=(type=char(40) updatewhereclause=yes name=employee_name dbname=~"employee_name~") column=(type=char(40) updatewhereclause=yes name=department dbname=~"department~") column=(type=char(20) updatewhereclause=yes name=city dbname=~"city~") column=(type=char(20) updatewhereclause=yes name=status dbname=~"status~") column=(type=char(100) updatewhereclause=yes name=email dbname=~"email~") column=(type=char(10) updatewhereclause=yes name=hire_date dbname=~"hire_date~")) text(band=header alignment=~"0~" text=~"ID~" border=~"0~" color=~"33554432~" x=~"0~" y=~"8~" height=~"88~" width=~"220~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_employee_id accessiblename=~"ID~") column(band=detail id=1 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"0~" y=~"8~" height=~"88~" width=~"220~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=employee_id format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"ID~") text(band=header alignment=~"0~" text=~"姓名~" border=~"0~" color=~"33554432~" x=~"220~" y=~"8~" height=~"88~" width=~"500~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_employee_name accessiblename=~"姓名~") column(band=detail id=2 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"220~" y=~"8~" height=~"88~" width=~"500~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=employee_name format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"姓名~") text(band=header alignment=~"0~" text=~"部门~" border=~"0~" color=~"33554432~" x=~"720~" y=~"8~" height=~"88~" width=~"480~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_department accessiblename=~"部门~") column(band=detail id=3 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"720~" y=~"8~" height=~"88~" width=~"480~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=department format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"部门~") text(band=header alignment=~"0~" text=~"城市~" border=~"0~" color=~"33554432~" x=~"1200~" y=~"8~" height=~"88~" width=~"420~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_city accessiblename=~"城市~") column(band=detail id=4 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"1200~" y=~"8~" height=~"88~" width=~"420~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=city format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"城市~") text(band=header alignment=~"0~" text=~"状态~" border=~"0~" color=~"33554432~" x=~"1620~" y=~"8~" height=~"88~" width=~"420~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_status accessiblename=~"状态~") column(band=detail id=5 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"1620~" y=~"8~" height=~"88~" width=~"420~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=status format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"状态~") text(band=header alignment=~"0~" text=~"邮箱~" border=~"0~" color=~"33554432~" x=~"2040~" y=~"8~" height=~"88~" width=~"1350~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_email accessiblename=~"邮箱~") column(band=detail id=6 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"2040~" y=~"8~" height=~"88~" width=~"1350~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=email format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"邮箱~") text(band=header alignment=~"0~" text=~"入职日期~" border=~"0~" color=~"33554432~" x=~"3390~" y=~"8~" height=~"88~" width=~"650~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=t_hire_date accessiblename=~"入职日期~") column(band=detail id=7 alignment=~"0~" tabsequence=0 border=~"0~" color=~"33554432~" x=~"3390~" y=~"8~" height=~"88~" width=~"650~" font.face=~"Microsoft YaHei UI~" font.height=~"-10~" font.weight=~"400~" background.mode=~"1~" name=hire_date format=~"[general]~" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes protect=~"1~" accessiblename=~"入职日期~") "
if dw_employees.Create(ls_syntax, ls_error) <> 1 then
    is_error = "DataWindow 创建失败：" + ls_error
    st_title.Text = is_error
    return false
end if
ib_ready = true
of_showpage(1)
return true
end function

public subroutine of_showpage (long al_page);
long ll_row, ll_id, ll_start, ll_slot, ll_number, ll_month, ll_day
string ls_departments[] = {"研发部", "产品部", "市场部", "销售部", "人事部"}
string ls_cities[] = {"北京", "上海", "广州", "深圳", "杭州"}
string ls_statuses[] = {"在职", "离职", "待入职"}
commandbutton lcb_page
if not ib_ready then return
il_page = Max(1, Min(50, al_page))
ll_start = (il_page - 1) * 20 + 1
dw_employees.SetRedraw(false)
dw_employees.Reset()
for ll_id = ll_start to ll_start + 19
    ll_row = dw_employees.InsertRow(0)
    dw_employees.SetItem(ll_row, "employee_id", ll_id)
    dw_employees.SetItem(ll_row, "employee_name", "用户" + String(ll_id))
    dw_employees.SetItem(ll_row, "department", ls_departments[Mod(ll_id, 5) + 1])
    dw_employees.SetItem(ll_row, "city", ls_cities[Mod(ll_id, 5) + 1])
    dw_employees.SetItem(ll_row, "status", ls_statuses[Mod(ll_id, 3) + 1])
    dw_employees.SetItem(ll_row, "email", "user" + String(ll_id) + "@example.com")
    ll_month = Mod(ll_id, 12) + 1
    ll_day = Mod(ll_id, 28) + 1
    dw_employees.SetItem(ll_row, "hire_date", "2024-" + String(ll_month, "00") + "-" + String(ll_day, "00"))
next
dw_employees.SetRow(1)
dw_employees.SetRedraw(true)
st_page.Text = "第 " + String(il_page) + " / 50 页；记录 " + String(ll_start) + "–" + String(ll_start+19) + " / 1000"
st_page.AccessibleName = st_page.Text
cb_first.Enabled = il_page > 1
cb_previous.Enabled = il_page > 1
cb_next.Enabled = il_page < 50
cb_last.Enabled = il_page < 50
ll_start = Max(1, Min(46, il_page - 2))
for ll_slot = 1 to 5
    choose case ll_slot
        case 1
            lcb_page = cb_page1
        case 2
            lcb_page = cb_page2
        case 3
            lcb_page = cb_page3
        case 4
            lcb_page = cb_page4
        case 5
            lcb_page = cb_page5
    end choose
    ll_number = ll_start + ll_slot - 1
    lcb_page.Text = String(ll_number)
    lcb_page.AccessibleName = lcb_page.Text
    lcb_page.Enabled = ll_number <> il_page
next
end subroutine

public subroutine of_scale_data (double ad_scale);
string ls_objects[] = {"employee_id", "employee_name", "department", "city", "status", "email", "hire_date", "t_employee_id", "t_employee_name", "t_department", "t_city", "t_status", "t_email", "t_hire_date"}
string ls_properties[] = {"X", "Y", "Width", "Height"}
string ls_property, ls_changes, ls_error
long ll_object, ll_property, ll_value
if not ib_ready then return
dw_employees.SetRedraw(false)
for ll_object = 1 to UpperBound(ls_objects)
    for ll_property = 1 to UpperBound(ls_properties)
        ls_property = ls_objects[ll_object] + "." + ls_properties[ll_property]
        ll_value = Long(Double(dw_employees.Describe(ls_property)) * ad_scale)
        ls_changes += ls_property + "=" + String(ll_value) + " "
    next
next
ls_changes += "DataWindow.Header.Height=" + String(Long(120 * ad_scale)) + " DataWindow.Detail.Height=" + String(Long(100 * ad_scale))
ls_error = dw_employees.Modify(ls_changes)
if ls_error <> "" then
    is_error = "DataWindow 布局失败：" + ls_error
    st_title.Text = is_error
end if
dw_employees.SetRedraw(true)
end subroutine

on u_table.create

this.st_title=create st_title
this.dw_employees=create dw_employees
this.st_page=create st_page
this.cb_first=create cb_first
this.cb_previous=create cb_previous
this.cb_page1=create cb_page1
this.cb_page2=create cb_page2
this.cb_page3=create cb_page3
this.cb_page4=create cb_page4
this.cb_page5=create cb_page5
this.cb_next=create cb_next
this.cb_last=create cb_last
this.Control[]={this.st_title,this.dw_employees,this.st_page,this.cb_first,this.cb_previous,this.cb_page1,this.cb_page2,this.cb_page3,this.cb_page4,this.cb_page5,this.cb_next,this.cb_last}
end on

on u_table.destroy

destroy(this.st_title)
destroy(this.dw_employees)
destroy(this.st_page)
destroy(this.cb_first)
destroy(this.cb_previous)
destroy(this.cb_page1)
destroy(this.cb_page2)
destroy(this.cb_page3)
destroy(this.cb_page4)
destroy(this.cb_page5)
destroy(this.cb_next)
destroy(this.cb_last)
end on

type st_title from statictext within u_table
integer x = 100
integer y = 70
integer width = 4300
integer height = 120
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "员工数据：共 1000 条，每页 20 条（原生 DataWindow）"
string accessiblename = "员工数据：共 1000 条，每页 20 条（原生 DataWindow）"


end type

type dw_employees from datawindow within u_table
integer x = 100
integer y = 250
integer width = 4510
integer height = 2020
boolean border = true
boolean hscrollbar = true
boolean vscrollbar = true
string accessiblename = "员工数据表格"
string accessibledescription = "ID、姓名、部门、城市、状态、邮箱、入职日期；每页20条记录"
integer taborder = 10

end type

type st_page from statictext within u_table
integer x = 100
integer y = 2310
integer width = 4300
integer height = 110
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "第 1 / 50 页"
string accessiblename = "第 1 / 50 页"


end type

type cb_first from commandbutton within u_table
integer x = 100
integer y = 2470
integer width = 430
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "首页"
string accessiblename = "首页"


end type

event cb_first.clicked;
parent.of_showpage(1)
end event

type cb_previous from commandbutton within u_table
integer x = 570
integer y = 2470
integer width = 500
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "上一页"
string accessiblename = "上一页"


end type

event cb_previous.clicked;
parent.of_showpage(parent.il_page - 1)
end event

type cb_page1 from commandbutton within u_table
integer x = 1120
integer y = 2470
integer width = 320
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "1"
string accessiblename = "1"


end type

event cb_page1.clicked;
parent.of_showpage(Long(this.Text))
end event

type cb_page2 from commandbutton within u_table
integer x = 1480
integer y = 2470
integer width = 320
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "2"
string accessiblename = "2"


end type

event cb_page2.clicked;
parent.of_showpage(Long(this.Text))
end event

type cb_page3 from commandbutton within u_table
integer x = 1840
integer y = 2470
integer width = 320
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "3"
string accessiblename = "3"


end type

event cb_page3.clicked;
parent.of_showpage(Long(this.Text))
end event

type cb_page4 from commandbutton within u_table
integer x = 2200
integer y = 2470
integer width = 320
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "4"
string accessiblename = "4"


end type

event cb_page4.clicked;
parent.of_showpage(Long(this.Text))
end event

type cb_page5 from commandbutton within u_table
integer x = 2560
integer y = 2470
integer width = 320
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "5"
string accessiblename = "5"


end type

event cb_page5.clicked;
parent.of_showpage(Long(this.Text))
end event

type cb_next from commandbutton within u_table
integer x = 3000
integer y = 2470
integer width = 500
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "下一页"
string accessiblename = "下一页"


end type

event cb_next.clicked;
parent.of_showpage(parent.il_page + 1)
end event

type cb_last from commandbutton within u_table
integer x = 3550
integer y = 2470
integer width = 430
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "末页"
string accessiblename = "末页"


end type

event cb_last.clicked;
parent.of_showpage(50)
end event
