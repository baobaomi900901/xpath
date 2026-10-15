unit MainForm;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, ExtCtrls, ComCtrls, Menus, Clipbrd, CommCtrl;

const
  EMPLOYEE_PAGE_SIZE = 100;
  EMPLOYEE_PAGE_COUNT = 10;
  EMPLOYEE_VISIBLE_PAGES = 5;
  FORM_ITEM_COUNT = 10;

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
    FFormItems: array[0..FORM_ITEM_COUNT - 1] of TPanel;

    FNameEdit: TEdit;
    FPasswordEdit: TEdit;
    FEmailEdit: TEdit;
    FAgeEdit: TEdit;
    FAgeSpin: TUpDown;
    FCityCombo: THs08ComboBox;
    FCityChecks: array[0..4] of TCheckBox;
    FGenderRadios: array[0..2] of TRadioButton;
    FHobbyChecks: array[0..3] of TCheckBox;
    FRemarkEdit: TMemo;
    FAgreeCheck: TCheckBox;
    FSaveButton: TButton;
    FResetButton: TButton;
    FPopupButton: TButton;
    FPopupStatus: TStaticText;
    FContextMenu: TPopupMenu;
    FActionPopup: TPopupMenu;

    FEmployeeList: TListView;
    FTablePager: TPanel;
    FTablePageInfo: TStaticText;
    FTableFirst: TButton;
    FTablePrevious: TButton;
    FTableNext: TButton;
    FTableLast: TButton;
    FTablePages: array[1..EMPLOYEE_VISIBLE_PAGES] of TButton;
    FTableCurrentPage: Integer;

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
    function CreateFormItem(AIndex: Integer; const ACaption: string; ATop, AHeight: Integer): TPanel;
    procedure BuildTablePage;
    procedure ShowEmployeePage(APage: Integer);
    procedure TablePageClick(Sender: TObject);
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
    procedure MainFormShow(Sender: TObject);
    procedure MainMenuClick(Sender: TObject);
  protected
    procedure CreateParams(var Params: TCreateParams); override;
  public
    constructor Create(AOwner: TComponent); override;
    destructor Destroy; override;
  end;

var
  RangeMainForm: TMainForm;

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
  ID_AGREE_CHECK = 1006;
  ID_SAVE_BUTTON = 1007;
  ID_RESET_BUTTON = 1008;
  ID_AGE_SPIN = 1009;
  ID_POPUP_STATUS = 1011;
  ID_FORM_HEADING = 1012;
  ID_FORM_ITEM_BASE = 4000;
  ID_FORM_LABEL_BASE = 4100;
  ID_CITY_CHECK_BASE = 4200;
  ID_GENDER_RADIO_BASE = 4300;
  ID_HOBBY_CHECK_BASE = 4400;
  ID_DRAG_TARGET = 2001;
  ID_DRAG_RESET = 2002;
  ID_DRAG_COPY = 2003;
  ID_DRAG_HIDE = 2004;
  ID_EMPLOYEE_LIST = 3001;
  ID_TABLE_PAGER = 3002;
  ID_TABLE_PAGE_INFO = 3003;
  ID_TABLE_FIRST = 3004;
  ID_TABLE_PREVIOUS = 3005;
  ID_TABLE_NEXT = 3006;
  ID_TABLE_LAST = 3007;
  ID_TABLE_PAGE_BASE = 3100;

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
  if Assigned(AControl) then
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
  OnShow := MainFormShow;
end;

procedure TMainForm.CreateParams(var Params: TCreateParams);
begin
  inherited CreateParams(Params);
  { CreateNew bypasses the VCL main-form flag used by MainFormOnTaskbar. }
  Params.WndParent := 0;
end;

procedure TMainForm.MainFormShow(Sender: TObject);
begin
  if Assigned(FLayoutForm) then
    Exit;
  { Application.MainForm is assigned after the main constructor returns. }
  FLayoutForm := TLayoutForm.Create(Self);
  FLayoutForm.Caption := 'ETF交易日期管理';
  FLayoutForm.FormStyle := fsMDIChild;
  FLayoutForm.BorderStyle := bsNone;
  FLayoutForm.Show;
  FLayoutForm.WindowState := wsMaximized;
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
  OnResize := LayoutControls;
  LayoutControls(Self);
end;

procedure TLayoutForm.BuildFormPage;
var
  Heading: TStaticText;
  Item: TPanel;
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

  Heading := TStaticText.Create(FContentPanel);
  Heading.Parent := FContentPanel;
  Heading.Caption := '用户信息表单';
  Heading.SetBounds(30, 12, 240, 24);
  SetAutomationId(Heading, ID_FORM_HEADING);

  Item := CreateFormItem(0, '姓名', 48, 32);
  FNameEdit := TEdit.Create(Item);
  FNameEdit.Parent := Item;
  FNameEdit.SetBounds(150, 0, 450, 23);
  SetAutomationId(FNameEdit, ID_NAME_EDIT);

  Item := CreateFormItem(1, '密码', 88, 32);
  FPasswordEdit := TEdit.Create(Item);
  FPasswordEdit.Parent := Item;
  FPasswordEdit.SetBounds(150, 0, 450, 23);
  FPasswordEdit.PasswordChar := '*';
  SetAutomationId(FPasswordEdit, ID_PASSWORD_EDIT);

  Item := CreateFormItem(2, '邮箱', 128, 32);
  FEmailEdit := TEdit.Create(Item);
  FEmailEdit.Parent := Item;
  FEmailEdit.SetBounds(150, 0, 450, 23);
  SetAutomationId(FEmailEdit, ID_EMAIL_EDIT);

  Item := CreateFormItem(3, '年龄', 168, 32);
  FAgeEdit := TEdit.Create(Item);
  FAgeEdit.Parent := Item;
  FAgeEdit.SetBounds(150, 0, 140, 23);
  FAgeEdit.Text := '25';
  SetAutomationId(FAgeEdit, ID_AGE_EDIT);
  FAgeSpin := TUpDown.Create(Item);
  FAgeSpin.Parent := Item;
  FAgeSpin.SetBounds(266, 0, 24, 23);
  FAgeSpin.Associate := FAgeEdit;
  FAgeSpin.Min := 18;
  FAgeSpin.Max := 80;
  FAgeSpin.Position := 25;
  FAgeSpin.Thousands := False;
  SetAutomationId(FAgeSpin, ID_AGE_SPIN);

  Item := CreateFormItem(4, '城市（单选）', 208, 32);
  FCityCombo := THs08ComboBox.Create(Item);
  FCityCombo.Parent := Item;
  FCityCombo.SetBounds(150, 0, 250, 23);
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

  Item := CreateFormItem(5, '城市（多选）', 248, 32);
  for Index := 0 to 4 do
  begin
    FCityChecks[Index] := TCheckBox.Create(Item);
    FCityChecks[Index].Parent := Item;
    FCityChecks[Index].Caption := Cities[Index];
    FCityChecks[Index].SetBounds(150 + Index * 78, 0, 74, 25);
    SetAutomationId(FCityChecks[Index], ID_CITY_CHECK_BASE + Index + 1);
  end;

  Item := CreateFormItem(6, '性别（单选）', 288, 32);
  for Index := 0 to 2 do
  begin
    FGenderRadios[Index] := TRadioButton.Create(Item);
    FGenderRadios[Index].Parent := Item;
    FGenderRadios[Index].Caption := ChooseString(Index + 1, ['男', '女', '其他']);
    FGenderRadios[Index].SetBounds(150 + Index * 88, 0, 82, 25);
    FGenderRadios[Index].Checked := Index = 0;
    SetAutomationId(FGenderRadios[Index], ID_GENDER_RADIO_BASE + Index + 1);
  end;

  Item := CreateFormItem(7, '兴趣爱好（多选）', 328, 32);
  for Index := 0 to 3 do
  begin
    FHobbyChecks[Index] := TCheckBox.Create(Item);
    FHobbyChecks[Index].Parent := Item;
    FHobbyChecks[Index].Caption := ChooseString(Index + 1, ['阅读', '运动', '音乐', '旅行']);
    FHobbyChecks[Index].SetBounds(150 + Index * 88, 0, 82, 25);
    SetAutomationId(FHobbyChecks[Index], ID_HOBBY_CHECK_BASE + Index + 1);
  end;

  Item := CreateFormItem(8, '备注', 368, 80);
  FRemarkEdit := TMemo.Create(Item);
  FRemarkEdit.Parent := Item;
  FRemarkEdit.SetBounds(150, 0, 450, 76);
  SetAutomationId(FRemarkEdit, ID_REMARK_EDIT);

  Item := CreateFormItem(9, '协议', 460, 32);
  FAgreeCheck := TCheckBox.Create(Item);
  FAgreeCheck.Parent := Item;
  FAgreeCheck.Caption := '同意用户协议';
  FAgreeCheck.SetBounds(150, 0, 180, 25);
  SetAutomationId(FAgreeCheck, ID_AGREE_CHECK);

  FSaveButton := TButton.Create(FContentPanel);
  FSaveButton.Parent := FContentPanel;
  FSaveButton.Caption := '保存';
  FSaveButton.OnClick := FormSaveClick;
  SetAutomationId(FSaveButton, ID_SAVE_BUTTON);
  FResetButton := TButton.Create(FContentPanel);
  FResetButton.Parent := FContentPanel;
  FResetButton.Caption := '重置';
  FResetButton.OnClick := FormResetClick;
  SetAutomationId(FResetButton, ID_RESET_BUTTON);

  FPopupButton := TButton.Create(FContentPanel);
  FPopupButton.Parent := FContentPanel;
  FPopupButton.Caption := '展开菜单';
  FPopupButton.OnClick := PopupButtonClick;
  FPopupButton.Width := 120;
  SetAutomationId(FPopupButton, ID_POPUP_BUTTON);
  FPopupStatus := TStaticText.Create(FContentPanel);
  FPopupStatus.Parent := FContentPanel;
  FPopupStatus.Caption := '菜单测试: 尚未选择菜单项';
  FPopupStatus.AutoSize := False;
  FPopupStatus.Height := 24;
  SetAutomationId(FPopupStatus, ID_POPUP_STATUS);

  BuildContextMenu;
  BuildActionPopup;
  FContentPanel.OnResize := LayoutControls;
end;

function TLayoutForm.CreateFormItem(AIndex: Integer; const ACaption: string; ATop, AHeight: Integer): TPanel;
var
  LabelControl: TStaticText;
begin
  Result := TPanel.Create(FContentPanel);
  FFormItems[AIndex] := Result;
  Result.Parent := FContentPanel;
  Result.Caption := ACaption;
  Result.ShowCaption := False;
  Result.BevelOuter := bvNone;
  Result.TabOrder := AIndex;
  Result.SetBounds(30, ATop, 760, AHeight);
  SetAutomationId(Result, ID_FORM_ITEM_BASE + AIndex + 1);

  LabelControl := TStaticText.Create(Result);
  LabelControl.Parent := Result;
  LabelControl.Caption := ACaption;
  LabelControl.SetBounds(0, 4, 145, 24);
  SetAutomationId(LabelControl, ID_FORM_LABEL_BASE + AIndex + 1);
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
  Index, ButtonLeft: Integer;

  function AddPageButton(const ACaption: string; AWidth, APage, AId: Integer): TButton;
  begin
    Result := TButton.Create(FTablePager);
    Result.Parent := FTablePager;
    Result.Caption := ACaption;
    Result.SetBounds(ButtonLeft, 36, AWidth, 28);
    Result.Tag := APage;
    Result.OnClick := TablePageClick;
    SetAutomationId(Result, AId);
    Inc(ButtonLeft, AWidth + 6);
  end;

begin
  FTablePager := TPanel.Create(FTableTab);
  FTablePager.Parent := FTableTab;
  FTablePager.Align := alBottom;
  FTablePager.Height := 76;
  FTablePager.BevelOuter := bvNone;
  SetAutomationId(FTablePager, ID_TABLE_PAGER);

  FTablePageInfo := TStaticText.Create(FTablePager);
  FTablePageInfo.Parent := FTablePager;
  FTablePageInfo.AutoSize := False;
  FTablePageInfo.SetBounds(16, 8, 760, 20);
  SetAutomationId(FTablePageInfo, ID_TABLE_PAGE_INFO);

  ButtonLeft := 16;
  FTableFirst := AddPageButton('首页', 52, 1, ID_TABLE_FIRST);
  FTablePrevious := AddPageButton('上一页', 68, 1, ID_TABLE_PREVIOUS);
  for Index := Low(FTablePages) to High(FTablePages) do
    FTablePages[Index] := AddPageButton(IntToStr(Index), 36, Index, ID_TABLE_PAGE_BASE + Index);
  FTableNext := AddPageButton('下一页', 68, 2, ID_TABLE_NEXT);
  FTableLast := AddPageButton('末页', 52, EMPLOYEE_PAGE_COUNT, ID_TABLE_LAST);

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
  SetAutomationId(FEmployeeList, ID_EMPLOYEE_LIST);
  ShowEmployeePage(1);
end;

procedure TLayoutForm.ShowEmployeePage(APage: Integer);
var
  Row: TListItem;
  Index, FirstRecord, LastRecord, FirstPage, PageNumber: Integer;
begin
  if APage < 1 then APage := 1;
  if APage > EMPLOYEE_PAGE_COUNT then APage := EMPLOYEE_PAGE_COUNT;
  FTableCurrentPage := APage;
  FirstRecord := (APage - 1) * EMPLOYEE_PAGE_SIZE + 1;
  LastRecord := APage * EMPLOYEE_PAGE_SIZE;

  FEmployeeList.Items.BeginUpdate;
  try
    FEmployeeList.Items.Clear;
    for Index := FirstRecord to LastRecord do
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
  finally
    FEmployeeList.Items.EndUpdate;
  end;

  FTablePageInfo.Caption := Format('第 %d / %d 页 | 每页 %d 条 | 共 %d 条 | 当前 %d-%d 条',
    [FTableCurrentPage, EMPLOYEE_PAGE_COUNT, EMPLOYEE_PAGE_SIZE,
     EMPLOYEE_PAGE_COUNT * EMPLOYEE_PAGE_SIZE, FirstRecord, LastRecord]);
  FTableFirst.Enabled := FTableCurrentPage > 1;
  FTablePrevious.Enabled := FTableCurrentPage > 1;
  FTablePrevious.Tag := FTableCurrentPage - 1;
  FTableNext.Enabled := FTableCurrentPage < EMPLOYEE_PAGE_COUNT;
  FTableNext.Tag := FTableCurrentPage + 1;
  FTableLast.Enabled := FTableCurrentPage < EMPLOYEE_PAGE_COUNT;
  { Start sliding when the selected page reaches the third button. }
  FirstPage := FTableCurrentPage - 1;
  if FirstPage < 1 then FirstPage := 1;
  if FirstPage > EMPLOYEE_PAGE_COUNT - EMPLOYEE_VISIBLE_PAGES + 1 then
    FirstPage := EMPLOYEE_PAGE_COUNT - EMPLOYEE_VISIBLE_PAGES + 1;
  for Index := Low(FTablePages) to High(FTablePages) do
  begin
    PageNumber := FirstPage + Index - 1;
    FTablePages[Index].Caption := IntToStr(PageNumber);
    FTablePages[Index].Tag := PageNumber;
    FTablePages[Index].Enabled := PageNumber <> FTableCurrentPage;
  end;
end;

procedure TLayoutForm.TablePageClick(Sender: TObject);
begin
  ShowEmployeePage((Sender as TButton).Tag);
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
  FDragCopy.Width := 140;
  FDragCopy.OnClick := DragCopyClick;
  SetAutomationId(FDragCopy, ID_DRAG_COPY);
  FDragHide := TButton.Create(FDragTab);
  FDragHide.Parent := FDragTab;
  FDragHide.Caption := '隐藏 drag-target';
  FDragHide.Left := 30;
  FDragHide.Top := 195;
  FDragHide.Width := 200;
  FDragHide.OnClick := DragHideClick;
  SetAutomationId(FDragHide, ID_DRAG_HIDE);

  FDragArena := TPanel.Create(FDragTab);
  FDragArena.Parent := FDragTab;
  FDragArena.Left := 390;
  FDragArena.Top := 45;
  FDragArena.Width := 600;
  FDragArena.Height := 450;
  FDragArena.BevelOuter := bvLowered;
  CreateDragTarget;
  FDragTab.OnResize := LayoutControls;
  CenterDragTarget;
  UpdateDragLabels;
end;

procedure TLayoutForm.LayoutControls(Sender: TObject);
var
  EditWidth, ItemWidth, Index: Integer;
begin
  if Assigned(FSaveButton) then
  begin
    FSaveButton.Left := (FContentPanel.ClientWidth div 2) - 105;
    FSaveButton.Top := FContentPanel.ClientHeight - 50;
    FResetButton.Left := (FContentPanel.ClientWidth div 2) + 12;
    FResetButton.Top := FContentPanel.ClientHeight - 50;
    ItemWidth := FContentPanel.ClientWidth - 60;
    if ItemWidth < 630 then ItemWidth := 630;
    for Index := Low(FFormItems) to High(FFormItems) do
      FFormItems[Index].Width := ItemWidth;
    EditWidth := FContentPanel.ClientWidth - 380;
    if EditWidth > 450 then EditWidth := 450;
    if EditWidth < 180 then EditWidth := 180;
    FNameEdit.Width := EditWidth;
    FPasswordEdit.Width := EditWidth;
    FEmailEdit.Width := EditWidth;
    FRemarkEdit.Width := EditWidth;
    FPopupButton.Left := FContentPanel.ClientWidth - 150;
    FPopupButton.Top := 12;
    FPopupStatus.Left := 30;
    FPopupStatus.Top := 500;
    FPopupStatus.Width := ItemWidth;
  end;
  if Assigned(FDragArena) then
  begin
    FDragArena.Width := FDragTab.ClientWidth - FDragArena.Left - 30;
    FDragArena.Height := FDragTab.ClientHeight - FDragArena.Top - 30;
    if FDragArena.Width < 160 then FDragArena.Width := 160;
    if FDragArena.Height < 120 then FDragArena.Height := 120;
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
  MessageDlg('提交成功！', mtInformation, [mbOK], 0);
end;

procedure TLayoutForm.FormResetClick(Sender: TObject);
var
  Index: Integer;
begin
  FNameEdit.Clear;
  FPasswordEdit.Clear;
  FEmailEdit.Clear;
  FAgeEdit.Text := '25';
  FAgeSpin.Position := 25;
  FCityCombo.ItemIndex := 0;
  for Index := Low(FCityChecks) to High(FCityChecks) do
    FCityChecks[Index].Checked := False;
  for Index := Low(FGenderRadios) to High(FGenderRadios) do
    FGenderRadios[Index].Checked := Index = 0;
  for Index := Low(FHobbyChecks) to High(FHobbyChecks) do
    FHobbyChecks[Index].Checked := False;
  FRemarkEdit.Clear;
  FAgreeCheck.Checked := False;
  SetMenuStatus('表单 > 重置');
  FNameEdit.SetFocus;
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
