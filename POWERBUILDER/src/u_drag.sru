$PBExportHeader$u_drag.sru
forward
global type u_drag from userobject
end type
type st_title from statictext within u_drag
end type
type st_help from statictext within u_drag
end type
type uo_arena from u_arena within u_drag
end type
type st_state from statictext within u_drag
end type
type cb_reset from commandbutton within u_drag
end type
type cb_hide from commandbutton within u_drag
end type
type cb_copy from commandbutton within u_drag
end type
type st_result from statictext within u_drag
end type
end forward

global type u_drag from userobject
integer width = 4700
integer height = 2650
string text = "拖拽测试"
string accessiblename = "拖拽测试"
st_title st_title
st_help st_help
uo_arena uo_arena
st_state st_state
cb_reset cb_reset
cb_hide cb_hide
cb_copy cb_copy
st_result st_result
end type
global u_drag u_drag

forward prototypes
public subroutine of_update ()
end prototypes

public subroutine of_update ();
st_state.Text = "left / top（px）: " + String(UnitsToPixels(uo_arena.cb_target.X, XUnitsToPixels!)) + " / " + String(UnitsToPixels(uo_arena.cb_target.Y, YUnitsToPixels!)) + "~r~n~r~n投放次数: " + String(uo_arena.il_moves) + "~r~n~r~n尺寸: 120 × 80 px"
st_state.AccessibleName = st_state.Text
end subroutine

on u_drag.create

this.st_title=create st_title
this.st_help=create st_help
this.uo_arena=create uo_arena
this.st_state=create st_state
this.cb_reset=create cb_reset
this.cb_hide=create cb_hide
this.cb_copy=create cb_copy
this.st_result=create st_result
this.Control[]={this.st_title,this.st_help,this.uo_arena,this.st_state,this.cb_reset,this.cb_hide,this.cb_copy,this.st_result}
end on

on u_drag.destroy

destroy(this.st_title)
destroy(this.st_help)
destroy(this.uo_arena)
destroy(this.st_state)
destroy(this.cb_reset)
destroy(this.cb_hide)
destroy(this.cb_copy)
destroy(this.st_result)
end on

type st_title from statictext within u_drag
integer x = 100
integer y = 80
integer width = 4400
integer height = 120
integer textsize = -10
string facename = "Microsoft YaHei UI"
string text = "拖拽测试"
string accessiblename = "拖拽测试"
integer weight = 700

end type

type st_help from statictext within u_drag
integer x = 100
integer y = 250
integer width = 4400
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "拖动 drag-target 到区域内；坐标以像素显示，目标始终限制在区域内。"
string accessiblename = "拖动 drag-target 到区域内；坐标以像素显示，目标始终限制在区域内。"


end type

type uo_arena from u_arena within u_drag
integer x = 1750
integer y = 500
integer width = 2600
integer height = 1550
end type

type st_state from statictext within u_drag
integer x = 100
integer y = 520
integer width = 1500
integer height = 720
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "位置状态"
string accessiblename = "位置状态"


end type

type cb_reset from commandbutton within u_drag
integer x = 100
integer y = 1320
integer width = 1300
integer height = 145
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "重置位置"
string accessiblename = "重置位置"


end type

event cb_reset.clicked;
parent.uo_arena.of_reset()
parent.of_update()
end event

type cb_hide from commandbutton within u_drag
integer x = 100
integer y = 1530
integer width = 1300
integer height = 145
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "隐藏 drag-target"
string accessiblename = "隐藏 drag-target"


end type

event cb_hide.clicked;
parent.uo_arena.of_finish_drag(false)
parent.uo_arena.cb_target.Hide()
parent.of_update()
end event

type cb_copy from commandbutton within u_drag
integer x = 100
integer y = 1740
integer width = 1300
integer height = 145
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "复制当前结果"
string accessiblename = "复制当前结果"


end type

event cb_copy.clicked;
string ls_payload
ls_payload = parent.uo_arena.of_json()
Clipboard(ls_payload)
if Clipboard() = ls_payload then
parent.st_result.Text = "已复制 JSON 到剪贴板"
else
parent.st_result.Text = "复制失败"
end if
parent.st_result.AccessibleName = parent.st_result.Text
end event

type st_result from statictext within u_drag
integer x = 100
integer y = 2220
integer width = 4350
integer height = 260
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "拖拽统计记录实际投放次数；调用方等待时间需由调用方统计。"
string accessiblename = "拖拽统计记录实际投放次数；调用方等待时间需由调用方统计。"


end type
