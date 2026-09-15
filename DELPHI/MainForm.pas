unit MainForm;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, ExtCtrls, ComCtrls, Menus, Clipbrd, CommCtrl;

type
  TLayoutPanel = class(TPanel)
  protected
    procedure CreateParams(var Params: TCreateParams); override;
  end;

  TfrmETFDate = class(TPanel)
  protected
    procedure CreateParams(var Params: TCreateParams); override;
  end;

  TRzPanel = class(TPanel)
  protected
    procedure CreateParams(var Params: TCreateParams); override;
  end;

  THs08ComboBox = class(TComboBox)
  protected
    procedure CreateParams(var Params: TCreateParams); override;
  end;

  TLayoutForm = class(TForm)
  private
    FLayoutPanel: TLayoutPanel;
    FPageControl: TPageControl;
    FFormTab: TTabSheet;
    FTableTab: TTabSheet;
    FDragTab: TTabSheet;
    FFormHost: TfrmETFDate;
    FContentPanel: TRzPanel;

    FNameEdit: TEdit;
    FPasswordEdit: TEdit;
    FEmailEdit: TEdit;
    FAgeEdit: TEdit;
    FCityCombo: THs08ComboBox;
    FRemarkEdit: TMemo;
    FAgreeCheck: TCheckBox;
    FSaveButton: TButton;
    FResetButton: TButton;
    FPopupButton: TButton;
    FPopupStatus: TLabel;
    FContextMenu: TPopupMenu;
    FActionPopup: TPopupMenu;

    FEmployeeList: TListView;

    FDragHeading: TLabel;
    FDragPosition: TLabel;
    FDragResult: TLabel;
    FDragStatus: TLabel;
    FDragReset: TButton;
    FDragCopy: TButton;
    FDragHide: TButton;
    FDragArena: TPanel;
    FDragTarget: TButton;
    FDragging: Boolean;
    FDragOffsetX: Integer;
    FDragOffsetY: Integer;
    FDragStartedAt: Cardinal;
    FDragMoveCount: Integer;

    procedure BuildFormPage;
    procedure BuildTablePage;
    procedure BuildDragPage;
    procedure BuildContextMenu;
    procedure BuildActionPopup;
    procedure LayoutControls(Sender: TObject);
    procedure FormTabChanged(Sender: TObject);
    procedure ContextMenuClick(Sender: TObject);
    procedure ActionMenuClick(Sender: TObject);
    procedure FormSaveClick(Sender: TObject);
    procedure FormResetClick(Sender: TObject);
    procedure PopupButtonClick(Sender: TObject);
    procedure DragResetClick(Sender: TObject);
    procedure DragCopyClick(Sender: TObject);
    procedure DragHideClick(Sender: TObject);
    procedure DragTargetMouseDown(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
    procedure DragTargetMouseMove(Sender: TObject; Shift: TShiftState; X, Y: Integer);
    procedure DragTargetMouseUp(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
    procedure CreateDragTarget;
    procedure CenterDragTarget;
    procedure UpdateDragLabels;
    procedure SetMenuStatus(const Value: string);
  public
    constructor Create(AOwner: TComponent); override;
  end;

  TMainForm = class(TForm)
  private
    FMainMenu: TMainMenu;
    FLayoutForm: TLayoutForm;
    procedure BuildMainMenu;
    procedure MainMenuClick(Sender: TObject);
  public
    constructor Create(AOwner: TComponent); override;
    destructor Destroy; override;
  end;

var
  MainForm: TMainForm;

procedure SetAutomationId(AControl: TWinControl; AId: Integer);

implementation

const
  ID_LAYOUT_FORM = 65280;
  ID_LAYOUT_PANEL = 1508682;
  ID_PAGE_CONTROL = 2688164;
  ID_FORM_TAB = 14092350;
  ID_FORM_HOST = 3278048;
  ID_CONTENT_PANEL = 23332742;
  ID_CITY_COMBO = 2555932;
  ID_NAME_EDIT = 1001;
  ID_PASSWORD_EDIT = 1002;
  ID_EMAIL_EDIT = 1003;
  ID_AGE_EDIT = 1004;
  ID_REMARK_EDIT = 1005;
  ID_POPUP_BUTTON = 1010;
  ID_DRAG_TARGET = 2001;
  ID_DRAG_RESET = 2002;
  ID_DRAG_COPY = 2003;
  ID_DRAG_HIDE = 2004;

function ChooseString(Index: Integer; const Values: array of string): string;
begin
  if (Index >= 1) and (Index <= Length(Values)) then
    Result := Values[Index - 1]
  else
    Result := '';
end;

function ChooseInteger(Index: Integer; const Values: array of Integer): Integer;
begin
  if (Index >= 1) and (Index <= Length(Values)) then
    Result := Values[Index - 1]
  else
    Result := 0;
end;

procedure SetAutomationId(AControl: TWinControl; AId: Integer);
begin
  if Assigned(AControl) and AControl.HandleAllocated then
    SetWindowLong(AControl.Handle, GWL_ID, AId);
end;

procedure SetNamedWinClass(var Params: TCreateParams; const Name: string);
begin
  StrPCopy(Params.WinClassName, Name);
end;

procedure TLayoutPanel.CreateParams(var Params: TCreateParams);
begin
  inherited CreateParams(Params);
  SetNamedWinClass(Params, 'TLayoutPanel');
end;

procedure TfrmETFDate.CreateParams(var Params: TCreateParams);
begin
  inherited CreateParams(Params);
  SetNamedWinClass(Params, 'TfrmETFDate');
end;

procedure TRzPanel.CreateParams(var Params: TCreateParams);
begin
  inherited CreateParams(Params);
  SetNamedWinClass(Params, 'TRzPanel');
end;

procedure THs08ComboBox.CreateParams(var Params: TCreateParams);
begin
  inherited CreateParams(Params);
  SetNamedWinClass(Params, 'THs08ComboBox');
end;

constructor TMainForm.Create(AOwner: TComponent);
begin
  inherited CreateNew(AOwner);
  Caption := 'Delphi VCL 靶场 - UIA';
  FormStyle := fsMDIForm;
  Position := poScreenCenter;
  Width := 1100;
  Height := 760;
  Constraints.MinWidth := 900;
  Constraints.MinHeight := 680;
  BuildMainMenu;

  FLayoutForm := TLayoutForm.Create(Self);
  FLayoutForm.Caption := 'ETF交易日期管理';
  FLayoutForm.FormStyle := fsMDIChild;
  FLayoutForm.BorderStyle := bsNone;
  FLayoutForm.Align := alClient;
  FLayoutForm.Show;
  SetAutomationId(FLayoutForm, ID_LAYOUT_FORM);
end;

destructor TMainForm.Destroy;
begin
  FLayoutForm := nil;
  inherited Destroy;
end;

procedure TMainForm.BuildMainMenu;
var
  FileMenu, EditMenu, Item: TMenuItem;
begin
  FMainMenu := TMainMenu.Create(Self);
  Menu := FMainMenu;

  FileMenu := TMenuItem.Create(FMainMenu);
  FileMenu.Caption := '文件(&F)';
  FMainMenu.Items.Add(FileMenu);
  Item := TMenuItem.Create(FileMenu);
  Item.Caption := '新建(&N)';
  Item.Tag := 500;
  Item.OnClick := MainMenuClick;
  FileMenu.Add(Item);
  Item := TMenuItem.Create(FileMenu);
  Item.Caption := '打开(&O)';
  Item.Tag := 501;
  Item.OnClick := MainMenuClick;
  FileMenu.Add(Item);
  Item := TMenuItem.Create(FileMenu);
  Item.Caption := '保存(&S)';
  Item.Tag := 502;
  Item.OnClick := MainMenuClick;
  FileMenu.Add(Item);

  EditMenu := TMenuItem.Create(FMainMenu);
  EditMenu.Caption := '编辑(&E)';
  FMainMenu.Items.Add(EditMenu);
  Item := TMenuItem.Create(EditMenu);
  Item.Caption := '撤销(&U)';
  Item.Tag := 510;
  Item.OnClick := MainMenuClick;
  EditMenu.Add(Item);
  Item := TMenuItem.Create(EditMenu);
  Item.Caption := '剪切(&T)';
  Item.Tag := 511;
  Item.OnClick := MainMenuClick;
  EditMenu.Add(Item);
  Item := TMenuItem.Create(EditMenu);
  Item.Caption := '复制(&C)';
  Item.Tag := 512;
  Item.OnClick := MainMenuClick;
  EditMenu.Add(Item);
  Item := TMenuItem.Create(EditMenu);
  Item.Caption := '粘贴(&P)';
  Item.Tag := 513;
  Item.OnClick := MainMenuClick;
  EditMenu.Add(Item);
  Item := TMenuItem.Create(EditMenu);
  Item.Caption := '全选(&A)';
  Item.Tag := 514;
  Item.OnClick := MainMenuClick;
  EditMenu.Add(Item);
end;

procedure TMainForm.MainMenuClick(Sender: TObject);
var
  Item: TMenuItem;
begin
  Item := Sender as TMenuItem;
  if Assigned(FLayoutForm) then
    FLayoutForm.SetMenuStatus('顶部菜单 > ' + StringReplace(Item.Caption, '&', '', [rfReplaceAll]));
end;

constructor TLayoutForm.Create(AOwner: TComponent);
begin
  inherited CreateNew(AOwner);
  FormStyle := fsMDIChild;
  BorderStyle := bsNone;
  Width := 1060;
  Height := 680;
  SetAutomationId(Self, ID_LAYOUT_FORM);

  FLayoutPanel := TLayoutPanel.Create(Self);
  FLayoutPanel.Parent := Self;
  FLayoutPanel.Align := alClient;
  FLayoutPanel.BevelOuter := bvNone;
  SetAutomationId(FLayoutPanel, ID_LAYOUT_PANEL);

  FPageControl := TPageControl.Create(FLayoutPanel);
  FPageControl.Parent := FLayoutPanel;
  FPageControl.Align := alClient;
  FPageControl.OnChange := FormTabChanged;
  SetAutomationId(FPageControl, ID_PAGE_CONTROL);

  FFormTab := TTabSheet.Create(FPageControl);
  FFormTab.PageControl := FPageControl;
  FFormTab.Caption := '表单控件';
  SetAutomationId(FFormTab, ID_FORM_TAB);

  FTableTab := TTabSheet.Create(FPageControl);
  FTableTab.PageControl := FPageControl;
  FTableTab.Caption := '表格数据';

  FDragTab := TTabSheet.Create(FPageControl);
  FDragTab.PageControl := FPageControl;
  FDragTab.Caption := '拖拽测试';

  BuildFormPage;
  BuildTablePage;
  BuildDragPage;
  FPageControl.ActivePage := FFormTab;
end;

procedure TLayoutForm.BuildFormPage;
var
  LabelControl: TLabel;
  Cities: array[0..4] of string;
  Index: Integer;
begin
  FFormHost := TfrmETFDate.Create(FFormTab);
  FFormHost.Parent := FFormTab;
  FFormHost.Align := alClient;
  FFormHost.BevelOuter := bvNone;
  SetAutomationId(FFormHost, ID_FORM_HOST);

  FContentPanel := TRzPanel.Create(FFormHost);
  FContentPanel.Parent := FFormHost;
  FContentPanel.Align := alClient;
  FContentPanel.BevelOuter := bvNone;
  SetAutomationId(FContentPanel, ID_CONTENT_PANEL);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '用户信息表单';
  LabelControl.Left := 30;
  LabelControl.Top := 12;
  LabelControl.AutoSize := True;

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '姓名';
  LabelControl.Left := 30;
  LabelControl.Top := 52;
  FNameEdit := TEdit.Create(FContentPanel);
  FNameEdit.Parent := FContentPanel;
  FNameEdit.Left := 180;
  FNameEdit.Top := 48;
  FNameEdit.Width := 450;
  FNameEdit.Anchors := [akLeft, akTop, akRight];
  SetAutomationId(FNameEdit, ID_NAME_EDIT);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '密码';
  LabelControl.Left := 30;
  LabelControl.Top := 92;
  FPasswordEdit := TEdit.Create(FContentPanel);
  FPasswordEdit.Parent := FContentPanel;
  FPasswordEdit.Left := 180;
  FPasswordEdit.Top := 88;
  FPasswordEdit.Width := 450;
  FPasswordEdit.PasswordChar := '*';
  FPasswordEdit.Anchors := [akLeft, akTop, akRight];
  SetAutomationId(FPasswordEdit, ID_PASSWORD_EDIT);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '邮箱';
  LabelControl.Left := 30;
  LabelControl.Top := 132;
  FEmailEdit := TEdit.Create(FContentPanel);
  FEmailEdit.Parent := FContentPanel;
  FEmailEdit.Left := 180;
  FEmailEdit.Top := 128;
  FEmailEdit.Width := 450;
  FEmailEdit.Anchors := [akLeft, akTop, akRight];
  SetAutomationId(FEmailEdit, ID_EMAIL_EDIT);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '年龄';
  LabelControl.Left := 30;
  LabelControl.Top := 172;
  FAgeEdit := TEdit.Create(FContentPanel);
  FAgeEdit.Parent := FContentPanel;
  FAgeEdit.Left := 180;
  FAgeEdit.Top := 168;
  FAgeEdit.Width := 140;
  FAgeEdit.Text := '25';
  SetAutomationId(FAgeEdit, ID_AGE_EDIT);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '城市（单选）';
  LabelControl.Left := 30;
  LabelControl.Top := 212;
  FCityCombo := THs08ComboBox.Create(FContentPanel);
  FCityCombo.Parent := FContentPanel;
  FCityCombo.Left := 180;
  FCityCombo.Top := 208;
  FCityCombo.Width := 250;
  FCityCombo.Style := csDropDownList;
  Cities[0] := '北京';
  Cities[1] := '上海';
  Cities[2] := '广州';
  Cities[3] := '深圳';
  Cities[4] := '杭州';
  for Index := Low(Cities) to High(Cities) do
    FCityCombo.Items.Add(Cities[Index]);
  FCityCombo.ItemIndex := 0;
  SetAutomationId(FCityCombo, ID_CITY_COMBO);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '城市（多选）';
  LabelControl.Left := 30;
  LabelControl.Top := 252;
  for Index := 0 to 4 do
  begin
    with TCheckBox.Create(FContentPanel) do
    begin
      Parent := FContentPanel;
      Caption := Cities[Index];
      Left := 180 + Index * 78;
      Top := 248;
      Width := 74;
    end;
  end;

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '性别（单选）';
  LabelControl.Left := 30;
  LabelControl.Top := 292;
  for Index := 0 to 2 do
  begin
    with TRadioButton.Create(FContentPanel) do
    begin
      Parent := FContentPanel;
      Caption := ChooseString(Index + 1, ['男', '女', '其他']);
      Left := 180 + Index * 88;
      Top := 288;
      Width := 82;
      if Index = 0 then Checked := True;
    end;
  end;

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '兴趣爱好（多选）';
  LabelControl.Left := 30;
  LabelControl.Top := 332;
  for Index := 0 to 3 do
  begin
    with TCheckBox.Create(FContentPanel) do
    begin
      Parent := FContentPanel;
      Caption := ChooseString(Index + 1, ['阅读', '运动', '音乐', '旅行']);
      Left := 180 + Index * 88;
      Top := 328;
      Width := 82;
    end;
  end;

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '备注';
  LabelControl.Left := 30;
  LabelControl.Top := 372;
  FRemarkEdit := TMemo.Create(FContentPanel);
  FRemarkEdit.Parent := FContentPanel;
  FRemarkEdit.Left := 180;
  FRemarkEdit.Top := 368;
  FRemarkEdit.Width := 450;
  FRemarkEdit.Height := 76;
  FRemarkEdit.Anchors := [akLeft, akTop, akRight];
  SetAutomationId(FRemarkEdit, ID_REMARK_EDIT);

  LabelControl := TLabel.Create(FContentPanel);
  LabelControl.Parent := FContentPanel;
  LabelControl.Caption := '协议';
  LabelControl.Left := 30;
  LabelControl.Top := 464;
  FAgreeCheck := TCheckBox.Create(FContentPanel);
  FAgreeCheck.Parent := FContentPanel;
  FAgreeCheck.Caption := '同意用户协议';
  FAgreeCheck.Left := 180;
  FAgreeCheck.Top := 460;
  FAgreeCheck.Width := 180;

  FSaveButton := TButton.Create(FContentPanel);
  FSaveButton.Parent := FContentPanel;
  FSaveButton.Caption := '保存';
  FSaveButton.OnClick := FormSaveClick;
  FResetButton := TButton.Create(FContentPanel);
  FResetButton.Parent := FContentPanel;
  FResetButton.Caption := '重置';
  FResetButton.OnClick := FormResetClick;

  FPopupButton := TButton.Create(FContentPanel);
  FPopupButton.Parent := FContentPanel;
  FPopupButton.Caption := '展开菜单';
  FPopupButton.OnClick := PopupButtonClick;
  FPopupButton.Anchors := [akTop, akRight];
  SetAutomationId(FPopupButton, ID_POPUP_BUTTON);
  FPopupStatus := TLabel.Create(FContentPanel);
  FPopupStatus.Parent := FContentPanel;
  FPopupStatus.Caption := '菜单测试: 尚未选择菜单项';
  FPopupStatus.Anchors := [akTop, akRight];

  BuildContextMenu;
  BuildActionPopup;
  FFormTab.OnResize := LayoutControls;
end;

procedure TLayoutForm.BuildContextMenu;
var
  Item: TMenuItem;
begin
  FContextMenu := TPopupMenu.Create(Self);
  Item := TMenuItem.Create(FContextMenu);
  Item.Caption := '撤销';
  Item.Tag := 1;
  Item.OnClick := ContextMenuClick;
  FContextMenu.Items.Add(Item);
  Item := TMenuItem.Create(FContextMenu);
  Item.Caption := '剪切';
  Item.Tag := 2;
  Item.OnClick := ContextMenuClick;
  FContextMenu.Items.Add(Item);
  Item := TMenuItem.Create(FContextMenu);
  Item.Caption := '复制';
  Item.Tag := 3;
  Item.OnClick := ContextMenuClick;
  FContextMenu.Items.Add(Item);
  Item := TMenuItem.Create(FContextMenu);
  Item.Caption := '粘贴';
  Item.Tag := 4;
  Item.OnClick := ContextMenuClick;
  FContextMenu.Items.Add(Item);
  Item := TMenuItem.Create(FContextMenu);
  Item.Caption := '全选';
  Item.Tag := 5;
  Item.OnClick := ContextMenuClick;
  FContextMenu.Items.Add(Item);
  FNameEdit.PopupMenu := FContextMenu;
  FPasswordEdit.PopupMenu := FContextMenu;
  FEmailEdit.PopupMenu := FContextMenu;
  FRemarkEdit.PopupMenu := FContextMenu;
  FCityCombo.PopupMenu := FContextMenu;
end;

procedure TLayoutForm.BuildActionPopup;
const
  Names: array[0..4] of string = ('打开', '复制', '重命名', '删除', '属性');
var
  Index: Integer;
  Item: TMenuItem;
begin
  FActionPopup := TPopupMenu.Create(Self);
  for Index := Low(Names) to High(Names) do
  begin
    Item := TMenuItem.Create(FActionPopup);
    Item.Caption := Names[Index];
    Item.Tag := Index;
    Item.OnClick := ActionMenuClick;
    FActionPopup.Items.Add(Item);
  end;
end;

procedure TLayoutForm.BuildTablePage;
var
  Column: TListColumn;
  Row: TListItem;
  Index: Integer;
begin
  FEmployeeList := TListView.Create(FTableTab);
  FEmployeeList.Parent := FTableTab;
  FEmployeeList.Align := alClient;
  FEmployeeList.ViewStyle := vsReport;
  FEmployeeList.RowSelect := True;
  for Index := 0 to 6 do
  begin
    Column := FEmployeeList.Columns.Add;
    Column.Caption := ChooseString(Index + 1, ['ID', '姓名', '部门', '城市', '状态', '邮箱', '入职日期']);
    Column.Width := ChooseInteger(Index + 1, [60, 110, 100, 90, 80, 220, 120]);
  end;
  for Index := 1 to 100 do
  begin
    Row := FEmployeeList.Items.Add;
    Row.Caption := IntToStr(Index);
    Row.SubItems.Add('用户' + IntToStr(Index));
    Row.SubItems.Add(ChooseString((Index mod 5) + 1, ['研发部', '产品部', '市场部', '销售部', '人事部']));
    Row.SubItems.Add(ChooseString((Index mod 5) + 1, ['北京', '上海', '广州', '深圳', '杭州']));
    Row.SubItems.Add(ChooseString((Index mod 3) + 1, ['在职', '离职', '待入职']));
    Row.SubItems.Add('user' + IntToStr(Index) + '@example.com');
    Row.SubItems.Add(Format('2024-%2.2d-%2.2d', [(Index mod 12) + 1, (Index mod 28) + 1]));
  end;
end;

procedure TLayoutForm.BuildDragPage;
begin
  FDragHeading := TLabel.Create(FDragTab);
  FDragHeading.Parent := FDragTab;
  FDragHeading.Caption := '元素拖拽测试';
  FDragHeading.Left := 30;
  FDragHeading.Top := 20;

  FDragPosition := TLabel.Create(FDragTab);
  FDragPosition.Parent := FDragTab;
  FDragPosition.Left := 30;
  FDragPosition.Top := 60;
  FDragPosition.AutoSize := True;
  FDragResult := TLabel.Create(FDragTab);
  FDragResult.Parent := FDragTab;
  FDragResult.Left := 30;
  FDragResult.Top := 90;
  FDragResult.AutoSize := True;
  FDragStatus := TLabel.Create(FDragTab);
  FDragStatus.Parent := FDragTab;
  FDragStatus.Left := 30;
  FDragStatus.Top := 120;
  FDragStatus.AutoSize := True;

  FDragReset := TButton.Create(FDragTab);
  FDragReset.Parent := FDragTab;
  FDragReset.Caption := '重置位置';
  FDragReset.Left := 30;
  FDragReset.Top := 155;
  FDragReset.OnClick := DragResetClick;
  SetAutomationId(FDragReset, ID_DRAG_RESET);
  FDragCopy := TButton.Create(FDragTab);
  FDragCopy.Parent := FDragTab;
  FDragCopy.Caption := '复制当前结果';
  FDragCopy.Left := 165;
  FDragCopy.Top := 155;
  FDragCopy.OnClick := DragCopyClick;
  SetAutomationId(FDragCopy, ID_DRAG_COPY);
  FDragHide := TButton.Create(FDragTab);
  FDragHide.Parent := FDragTab;
  FDragHide.Caption := '隐藏 drag-target';
  FDragHide.Left := 30;
  FDragHide.Top := 195;
  FDragHide.OnClick := DragHideClick;
  SetAutomationId(FDragHide, ID_DRAG_HIDE);

  FDragArena := TPanel.Create(FDragTab);
  FDragArena.Parent := FDragTab;
  FDragArena.Left := 390;
  FDragArena.Top := 45;
  FDragArena.Width := 600;
  FDragArena.Height := 450;
  FDragArena.BevelOuter := bvLowered;
  FDragArena.Anchors := [akLeft, akTop, akRight, akBottom];
  CreateDragTarget;
  FDragTab.OnResize := LayoutControls;
  CenterDragTarget;
  UpdateDragLabels;
end;

procedure TLayoutForm.LayoutControls(Sender: TObject);
begin
  if Assigned(FSaveButton) then
  begin
    FSaveButton.Left := (FContentPanel.ClientWidth div 2) - 105;
    FSaveButton.Top := FContentPanel.ClientHeight - 50;
    FResetButton.Left := (FContentPanel.ClientWidth div 2) + 12;
    FResetButton.Top := FContentPanel.ClientHeight - 50;
    FPopupButton.Left := FContentPanel.ClientWidth - 198;
    FPopupButton.Top := 12;
    FPopupStatus.Left := FContentPanel.ClientWidth - 348;
    FPopupStatus.Top := 50;
  end;
  if Assigned(FDragArena) then
  begin
    FDragArena.Width := FDragTab.ClientWidth - FDragArena.Left - 30;
    FDragArena.Height := FDragTab.ClientHeight - FDragArena.Top - 30;
    CenterDragTarget;
  end;
end;

procedure TLayoutForm.FormTabChanged(Sender: TObject);
begin
  if FPageControl.ActivePage = FDragTab then
    UpdateDragLabels;
end;

procedure TLayoutForm.FormSaveClick(Sender: TObject);
begin
  SetMenuStatus('表单 > 保存');
end;

procedure TLayoutForm.FormResetClick(Sender: TObject);
begin
  FNameEdit.Clear;
  FPasswordEdit.Clear;
  FEmailEdit.Clear;
  FAgeEdit.Text := '25';
  FCityCombo.ItemIndex := 0;
  FRemarkEdit.Clear;
  FAgreeCheck.Checked := False;
  SetMenuStatus('表单 > 重置');
end;

procedure TLayoutForm.PopupButtonClick(Sender: TObject);
var
  ScreenPoint: TPoint;
begin
  ScreenPoint := FPopupButton.ClientToScreen(Point(0, FPopupButton.Height));
  FActionPopup.Popup(ScreenPoint.X, ScreenPoint.Y);
end;

procedure TLayoutForm.ContextMenuClick(Sender: TObject);
begin
  SetMenuStatus('右键菜单 > ' + (Sender as TMenuItem).Caption);
end;

procedure TLayoutForm.ActionMenuClick(Sender: TObject);
begin
  SetMenuStatus('操作菜单 > ' + (Sender as TMenuItem).Caption);
end;

procedure TLayoutForm.SetMenuStatus(const Value: string);
begin
  if Assigned(FPopupStatus) then
    FPopupStatus.Caption := '菜单测试: ' + Value;
end;

procedure TLayoutForm.CreateDragTarget;
begin
  if Assigned(FDragTarget) then
    Exit;
  FDragTarget := TButton.Create(FDragArena);
  FDragTarget.Parent := FDragArena;
  FDragTarget.Caption := 'drag-target';
  FDragTarget.Width := 140;
  FDragTarget.Height := 80;
  FDragTarget.OnMouseDown := DragTargetMouseDown;
  FDragTarget.OnMouseMove := DragTargetMouseMove;
  FDragTarget.OnMouseUp := DragTargetMouseUp;
  SetAutomationId(FDragTarget, ID_DRAG_TARGET);
  FDragTarget.Visible := True;
end;

procedure TLayoutForm.CenterDragTarget;
begin
  if not Assigned(FDragTarget) then
    Exit;
  FDragTarget.Left := (FDragArena.ClientWidth - FDragTarget.Width) div 2;
  FDragTarget.Top := (FDragArena.ClientHeight - FDragTarget.Height) div 2;
end;

procedure TLayoutForm.UpdateDragLabels;
begin
  if not Assigned(FDragStatus) then
    Exit;
  if not Assigned(FDragTarget) then
  begin
    FDragStatus.Caption := '状态: 元素已隐藏';
    Exit;
  end;
  FDragPosition.Caption := Format('当前位置: left=%d, top=%d', [FDragTarget.Left, FDragTarget.Top]);
  FDragResult.Caption := Format('本次拖拽: move=%d', [FDragMoveCount]);
  if FDragging then
    FDragStatus.Caption := '状态: 拖拽中'
  else
    FDragStatus.Caption := '状态: 空闲';
end;

procedure TLayoutForm.DragResetClick(Sender: TObject);
begin
  CreateDragTarget;
  CenterDragTarget;
  FDragMoveCount := 0;
  FDragging := False;
  FDragHide.Enabled := True;
  UpdateDragLabels;
end;

procedure TLayoutForm.DragCopyClick(Sender: TObject);
begin
  if not Assigned(FDragTarget) then
  begin
    SetMenuStatus('拖拽 > 当前元素不存在');
    Exit;
  end;
  Clipboard.AsText := Format(
    '{"left":%d,"top":%d,"visible":true,"moveCount":%d}',
    [FDragTarget.Left, FDragTarget.Top, FDragMoveCount]
  );
  SetMenuStatus('拖拽 > 已复制当前结果');
end;

procedure TLayoutForm.DragHideClick(Sender: TObject);
begin
  if not Assigned(FDragTarget) then
    Exit;
  if FDragging then
  begin
    ReleaseCapture;
    FDragging := False;
  end;
  FDragTarget.Free;
  FDragTarget := nil;
  FDragHide.Enabled := False;
  UpdateDragLabels;
end;

procedure TLayoutForm.DragTargetMouseDown(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
begin
  if Button <> mbLeft then
    Exit;
  FDragging := True;
  FDragOffsetX := X;
  FDragOffsetY := Y;
  FDragStartedAt := GetTickCount;
  FDragMoveCount := 0;
  SetCapture(FDragTarget.Handle);
  FDragTarget.SetFocus;
  UpdateDragLabels;
end;

procedure TLayoutForm.DragTargetMouseMove(Sender: TObject; Shift: TShiftState; X, Y: Integer);
var
  Point: TPoint;
  NewLeft, NewTop, MaxLeft, MaxTop: Integer;
begin
  if not FDragging then
    Exit;
  GetCursorPos(Point);
  Point := FDragArena.ScreenToClient(Point);
  MaxLeft := FDragArena.ClientWidth - FDragTarget.Width;
  MaxTop := FDragArena.ClientHeight - FDragTarget.Height;
  NewLeft := Point.X - FDragOffsetX;
  NewTop := Point.Y - FDragOffsetY;
  if NewLeft < 0 then NewLeft := 0;
  if NewTop < 0 then NewTop := 0;
  if NewLeft > MaxLeft then NewLeft := MaxLeft;
  if NewTop > MaxTop then NewTop := MaxTop;
  if (NewLeft <> FDragTarget.Left) or (NewTop <> FDragTarget.Top) then
  begin
    FDragTarget.Left := NewLeft;
    FDragTarget.Top := NewTop;
    Inc(FDragMoveCount);
    UpdateDragLabels;
  end;
end;

procedure TLayoutForm.DragTargetMouseUp(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
begin
  if Button <> mbLeft then
    Exit;
  FDragging := False;
  ReleaseCapture;
  UpdateDragLabels;
end;

end.
