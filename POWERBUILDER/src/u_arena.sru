$PBExportHeader$u_arena.sru
forward
global type u_arena from userobject
end type
type cb_target from commandbutton within u_arena
end type
end forward

global type u_arena from userobject
integer width = 2600
integer height = 1550
boolean border = true
long backcolor = 15790320
string accessiblename = "拖拽区域"
cb_target cb_target
end type
global u_arena u_arena

type prototypes
function longptr win_setcapture(longptr hwnd) library "user32.dll" alias for "SetCapture"
function longptr win_getcapture() library "user32.dll" alias for "GetCapture"
function long win_releasecapture() library "user32.dll" alias for "ReleaseCapture"
end prototypes

type variables
long il_initial_x, il_initial_y, il_anchor_x, il_anchor_y, il_delta_x, il_delta_y, il_moves
long il_start_x, il_start_y
boolean ib_dragging = false
end variables

forward prototypes
public subroutine of_reset ()
public subroutine of_move (long al_x, long al_y)
public subroutine of_position (long al_x, long al_y)
public subroutine of_begin_drag (long al_anchor_x, long al_anchor_y)
public subroutine of_drag_to (long al_pointer_x, long al_pointer_y)
public subroutine of_finish_drag (boolean ab_commit)
public function string of_json ()
end prototypes

public subroutine of_reset ();
of_finish_drag(false)
cb_target.Resize(PixelsToUnits(120, XPixelsToUnits!), PixelsToUnits(80, YPixelsToUnits!))
il_initial_x = (this.Width - cb_target.Width) / 2
il_initial_y = (this.Height - cb_target.Height) / 2
cb_target.Move(il_initial_x, il_initial_y)
cb_target.Show()
il_moves = 0
il_delta_x = 0
il_delta_y = 0
il_anchor_x = cb_target.Width / 2
il_anchor_y = cb_target.Height / 2
end subroutine

public subroutine of_move (long al_x, long al_y);
long ll_before_x, ll_before_y
ll_before_x = cb_target.X
ll_before_y = cb_target.Y
of_position(al_x, al_y)
il_delta_x = cb_target.X - ll_before_x
il_delta_y = cb_target.Y - ll_before_y
il_moves ++
end subroutine

public subroutine of_position (long al_x, long al_y);
long ll_x, ll_y
// Move snaps PB units to native pixels. Reserve one pixel so rounding the
// returned X/Y cannot move the right/bottom edge beyond the arena.
ll_x = Max(0, Min(this.Width - cb_target.Width - PixelsToUnits(1, XPixelsToUnits!), al_x))
ll_y = Max(0, Min(this.Height - cb_target.Height - PixelsToUnits(1, YPixelsToUnits!), al_y))
cb_target.Move(ll_x, ll_y)
end subroutine

public subroutine of_begin_drag (long al_anchor_x, long al_anchor_y);
of_finish_drag(false)
il_anchor_x = Max(0, Min(cb_target.Width, al_anchor_x))
il_anchor_y = Max(0, Min(cb_target.Height, al_anchor_y))
il_start_x = cb_target.X
il_start_y = cb_target.Y
il_delta_x = 0
il_delta_y = 0
ib_dragging = true
end subroutine

public subroutine of_drag_to (long al_pointer_x, long al_pointer_y);
if not ib_dragging then return
of_position(al_pointer_x - il_anchor_x, al_pointer_y - il_anchor_y)
il_delta_x = cb_target.X - il_start_x
il_delta_y = cb_target.Y - il_start_y
end subroutine

public subroutine of_finish_drag (boolean ab_commit);
if not ib_dragging then return
// Clear first: ReleaseCapture can synchronously send WM_CAPTURECHANGED.
ib_dragging = false
if ab_commit then il_moves ++
if win_getcapture() = Handle(cb_target) then win_releasecapture()
end subroutine

public function string of_json ();
string ls_visible
ls_visible = "false"
if cb_target.Visible then ls_visible = "true"
return '{"visible":' + ls_visible + ',"left":' + String(UnitsToPixels(cb_target.X, XUnitsToPixels!)) + &
    ',"top":' + String(UnitsToPixels(cb_target.Y, YUnitsToPixels!)) + &
    ',"offset_left":' + String(UnitsToPixels(cb_target.X - il_initial_x, XUnitsToPixels!)) + &
    ',"offset_top":' + String(UnitsToPixels(cb_target.Y - il_initial_y, YUnitsToPixels!)) + &
    ',"delta_left":' + String(UnitsToPixels(il_delta_x, XUnitsToPixels!)) + &
    ',"delta_top":' + String(UnitsToPixels(il_delta_y, YUnitsToPixels!)) + &
    ',"anchor_x":' + String(UnitsToPixels(il_anchor_x, XUnitsToPixels!)) + &
    ',"anchor_y":' + String(UnitsToPixels(il_anchor_y, YUnitsToPixels!)) + &
    ',"drop_count":' + String(il_moves) + '}'
end function

on u_arena.create

this.cb_target=create cb_target
this.Control[]={this.cb_target}
end on

on u_arena.destroy

of_finish_drag(false)
destroy(this.cb_target)
end on

type cb_target from commandbutton within u_arena
integer x = 800
integer y = 400
integer width = 550
integer height = 320
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "drag-target"
string accessiblename = "drag-target"
boolean dragauto = false
integer taborder = 10
event ue_press pbm_lbuttondown
event ue_move pbm_mousemove
event ue_release pbm_lbuttonup
event ue_other pbm_other

end type

event cb_target.ue_press;
this.SetFocus()
parent.of_begin_drag(this.PointerX(), this.PointerY())
// Keep receiving movement and button-up outside the source rectangle.
parent.win_setcapture(Handle(this))
// This button is a drag source; skip its native click tracking/capture.
Message.Processed = true
Message.ReturnValue = 0
end event

event cb_target.ue_move;
u_drag lu_drag
if not parent.ib_dragging then return
if parent.win_getcapture() <> Handle(this) then
    parent.of_finish_drag(false)
    return
end if
parent.of_drag_to(this.X + this.PointerX(), this.Y + this.PointerY())
lu_drag = parent.GetParent()
lu_drag.of_update()
Message.Processed = true
Message.ReturnValue = 0
end event

event cb_target.ue_release;
u_drag lu_drag
if not parent.ib_dragging then return
parent.of_drag_to(this.X + this.PointerX(), this.Y + this.PointerY())
parent.of_finish_drag(true)
lu_drag = parent.GetParent()
lu_drag.of_update()
Message.Processed = true
Message.ReturnValue = 0
end event

event cb_target.ue_other;
// WM_CAPTURECHANGED / WM_CANCELMODE: an interrupted drag is not a drop.
if parent.ib_dragging and (Message.Number = 533 or Message.Number = 31) then
    parent.of_finish_drag(false)
end if
end event
