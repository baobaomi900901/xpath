unit ComplexControls;

interface

uses
  Windows, SysUtils, Classes, Controls, Forms, StdCtrls, ExtCtrls, ComCtrls,
  Grids, DB, DBClient, DBGrids, DBCtrls, VirtualTrees
  {$IFDEF WITH_DEVEXPRESS}
  , cxGrid, cxGridLevel, cxGridTableView, cxTL
  {$IFDEF DEVEXPRESS_TRIAL}
  , dxUIAClasses
  {$ENDIF}
  {$ENDIF};

type
  PEmployeeNode = ^TEmployeeNode;
  TEmployeeNode = record
    EmployeeId: Integer;
    Department: Integer;
  end;

  TComplexControlPages = class(TComponent)
  private
    FPages: TPageControl;
    FStringGrid: TStringGrid;
    FStringStatus: TStaticText;
    FData: TClientDataSet;
    FSource: TDataSource;
    FDBGrid: TDBGrid;
    FDBStatus: TStaticText;
    FSearch: TEdit;
    FVirtualTree: TVirtualStringTree;
    FVirtualStatus: TStaticText;
    FVirtualNames: array[1..1000] of string;
    {$IFDEF WITH_DEVEXPRESS}
    FCxGridView: TcxGridTableView;
    FCxTreeList: TcxTreeList;
    FCxGridStatus: TStaticText;
    FCxTreeStatus: TStaticText;
    procedure LoadCxGridData(Sender: TObject);
    procedure LoadCxTreeData;
    procedure CxTreeAction(Sender: TObject);
    {$ENDIF}
    function NewPage(const ACaption, ADescription: string; AId: Integer;
      out AToolbar: TPanel; out AStatus: TStaticText): TTabSheet;
    procedure AddButton(AParent: TWinControl; const ACaption: string;
      ALeft, AId, ATag: Integer; AClick: TNotifyEvent);
    procedure BuildStringGrid;
    procedure LoadStringGrid(Sender: TObject);
    procedure StringSelectCell(Sender: TObject; ACol, ARow: Integer; var CanSelect: Boolean);
    procedure StringSetEditText(Sender: TObject; ACol, ARow: Integer; const Value: string);
    procedure BuildDBGrid;
    procedure LoadData(Sender: TObject);
    procedure DataChanged(DataSet: TDataSet);
    procedure DataFilter(DataSet: TDataSet; var Accept: Boolean);
    procedure SearchChanged(Sender: TObject);
    procedure DBTitleClick(Column: TColumn);
    procedure BuildVirtualTree;
    procedure VirtualInitNode(Sender: TBaseVirtualTree; ParentNode, Node: PVirtualNode;
      var InitialStates: TVirtualNodeInitStates);
    procedure VirtualInitChildren(Sender: TBaseVirtualTree; Node: PVirtualNode; var ChildCount: Cardinal);
    procedure VirtualGetText(Sender: TBaseVirtualTree; Node: PVirtualNode;
      Column: TColumnIndex; TextType: TVSTTextType; var CellText: UnicodeString);
    procedure VirtualNewText(Sender: TBaseVirtualTree; Node: PVirtualNode;
      Column: TColumnIndex; NewText: UnicodeString);
    procedure VirtualEditing(Sender: TBaseVirtualTree; Node: PVirtualNode;
      Column: TColumnIndex; var Allowed: Boolean);
    procedure VirtualChanged(Sender: TBaseVirtualTree; Node: PVirtualNode);
    procedure VirtualAction(Sender: TObject);
    procedure BuildDevExpressPages;
  public
    constructor Create(AOwner: TComponent; APages: TPageControl); reintroduce;
  end;

implementation

uses MidasLib, VTAccessibility;

const
  HEADERS: array[0..6] of string = ('ID', '姓名', '部门', '城市', '状态', '邮箱', '入职日期');
  FIELD_NAMES: array[0..6] of string = ('ID', 'EmployeeName', 'Department', 'City', 'Status', 'Email', 'HireDate');
  WIDTHS: array[0..6] of Integer = (70, 130, 120, 100, 90, 240, 130);
  DEPARTMENTS: array[0..9] of string = ('研发部', '产品部', '市场部', '销售部', '人事部',
    '财务部', '运营部', '客服部', '测试部', '设计部');
  CITIES: array[0..4] of string = ('北京', '上海', '广州', '深圳', '杭州');
  STATUSES: array[0..2] of string = ('在职', '离职', '待入职');

procedure Identify(AControl: TWinControl; AId: Integer);
begin
  SetWindowLong(AControl.Handle, GWL_ID, AId);
end;

function EmployeeCell(AId, AColumn: Integer): string;
begin
  case AColumn of
    0: Result := IntToStr(AId);
    1: Result := '用户' + IntToStr(AId);
    2: Result := DEPARTMENTS[(AId - 1) div 100];
    3: Result := CITIES[(AId - 1) mod 5];
    4: Result := STATUSES[(AId - 1) mod 3];
    5: Result := 'user' + IntToStr(AId) + '@example.com';
    6: Result := Format('2024-%2.2d-%2.2d', [(AId mod 12) + 1, (AId mod 28) + 1]);
  else
    Result := '';
  end;
end;

constructor TComplexControlPages.Create(AOwner: TComponent; APages: TPageControl);
begin
  inherited Create(AOwner);
  FPages := APages;
  BuildStringGrid;
  BuildDBGrid;
  BuildVirtualTree;
  BuildDevExpressPages;
end;

function TComplexControlPages.NewPage(const ACaption, ADescription: string; AId: Integer;
  out AToolbar: TPanel; out AStatus: TStaticText): TTabSheet;
var
  Description: TStaticText;
begin
  Result := TTabSheet.Create(FPages);
  Result.PageControl := FPages;
  Result.Caption := ACaption;
  Identify(Result, AId);
  AToolbar := TPanel.Create(Result);
  AToolbar.Parent := Result;
  AToolbar.Align := alTop;
  AToolbar.Height := 76;
  AToolbar.BevelOuter := bvNone;
  Identify(AToolbar, AId + 1);
  Description := TStaticText.Create(AToolbar);
  Description.Parent := AToolbar;
  Description.SetBounds(12, 8, 1000, 24);
  Description.Caption := ADescription;
  Identify(Description, AId + 2);
  AStatus := TStaticText.Create(Result);
  AStatus.Parent := Result;
  AStatus.Align := alBottom;
  AStatus.AutoSize := False;
  AStatus.Height := 28;
  Identify(AStatus, AId + 3);
end;

procedure TComplexControlPages.AddButton(AParent: TWinControl; const ACaption: string;
  ALeft, AId, ATag: Integer; AClick: TNotifyEvent);
var
  Button: TButton;
begin
  Button := TButton.Create(AParent);
  Button.Parent := AParent;
  Button.SetBounds(ALeft, 38, 100, 28);
  Button.Caption := ACaption;
  Button.Tag := ATag;
  Button.OnClick := AClick;
  Identify(Button, AId);
end;

procedure TComplexControlPages.BuildStringGrid;
var
  Tab: TTabSheet;
  Toolbar: TPanel;
  Column: Integer;
begin
  Tab := NewPage('TStringGrid', '原生 TStringGrid：100 行；固定 ID 列，支持单元格编辑、键盘导航和列宽调整。',
    6000, Toolbar, FStringStatus);
  AddButton(Toolbar, '恢复数据', 12, 6011, 0, LoadStringGrid);
  FStringGrid := TStringGrid.Create(Tab);
  FStringGrid.Parent := Tab;
  FStringGrid.Align := alClient;
  FStringGrid.ColCount := 7;
  FStringGrid.RowCount := 101;
  FStringGrid.FixedCols := 1;
  FStringGrid.FixedRows := 1;
  FStringGrid.DefaultRowHeight := 24;
  FStringGrid.Options := FStringGrid.Options + [goEditing, goTabs, goColSizing];
  for Column := 0 to 6 do
    FStringGrid.ColWidths[Column] := WIDTHS[Column];
  Identify(FStringGrid, 6010);
  LoadStringGrid(nil);
  FStringGrid.OnSelectCell := StringSelectCell;
  FStringGrid.OnSetEditText := StringSetEditText;
end;

procedure TComplexControlPages.LoadStringGrid(Sender: TObject);
var
  Row, Column: Integer;
begin
  FStringGrid.EditorMode := False;
  for Column := 0 to 6 do
  begin
    FStringGrid.Cells[Column, 0] := HEADERS[Column];
    for Row := 1 to 100 do
      FStringGrid.Cells[Column, Row] := EmployeeCell(Row, Column);
  end;
  FStringGrid.Row := 1;
  FStringGrid.Col := 1;
  FStringGrid.TopRow := 1;
  FStringStatus.Caption := 'TStringGrid | 共 100 行、7 列 | 选中：ID 1，姓名=用户1';
end;

procedure TComplexControlPages.StringSelectCell(Sender: TObject; ACol, ARow: Integer; var CanSelect: Boolean);
begin
  FStringStatus.Caption := Format('TStringGrid | 共 100 行、7 列 | 选中：ID %s，%s=%s',
    [FStringGrid.Cells[0, ARow], HEADERS[ACol], FStringGrid.Cells[ACol, ARow]]);
end;

procedure TComplexControlPages.StringSetEditText(Sender: TObject; ACol, ARow: Integer; const Value: string);
begin
  FStringStatus.Caption := Format('TStringGrid | 已编辑：ID %d，%s=%s', [ARow, HEADERS[ACol], Value]);
end;

procedure TComplexControlPages.BuildDBGrid;
var
  Tab: TTabSheet;
  Toolbar: TPanel;
  Navigator: TDBNavigator;
  Column: TColumn;
  Index: Integer;
begin
  Tab := NewPage('TDBGrid', '原生 TDBGrid + 内存数据集：1000 条；可编辑、筛选、点击列头排序，修改仅保存在内存。',
    6100, Toolbar, FDBStatus);
  FSearch := TEdit.Create(Toolbar);
  FSearch.Parent := Toolbar;
  FSearch.SetBounds(12, 40, 220, 24);
  FSearch.TextHint := '筛选姓名 / 城市 / 邮箱';
  Identify(FSearch, 6111);
  AddButton(Toolbar, '恢复数据', 244, 6112, 0, LoadData);
  FData := TClientDataSet.Create(Self);
  FData.FieldDefs.Add('ID', ftInteger);
  for Index := 1 to 5 do
    FData.FieldDefs.Add(FIELD_NAMES[Index], ftWideString, 120);
  FData.FieldDefs.Add('HireDate', ftDate);
  FData.OnFilterRecord := DataFilter;
  FData.AfterScroll := DataChanged;
  FData.AfterPost := DataChanged;
  FSource := TDataSource.Create(Self);
  FSource.DataSet := FData;
  Navigator := TDBNavigator.Create(Toolbar);
  Navigator.Parent := Toolbar;
  Navigator.SetBounds(360, 38, 360, 28);
  Navigator.DataSource := FSource;
  Navigator.VisibleButtons := [nbFirst, nbPrior, nbNext, nbLast, nbEdit, nbPost, nbCancel];
  Identify(Navigator, 6113);
  FDBGrid := TDBGrid.Create(Tab);
  FDBGrid.Parent := Tab;
  FDBGrid.Align := alClient;
  FDBGrid.DataSource := FSource;
  FDBGrid.Options := FDBGrid.Options + [dgEditing, dgTitles, dgColLines, dgRowLines, dgColumnResize];
  for Index := 0 to 6 do
  begin
    Column := FDBGrid.Columns.Add;
    Column.FieldName := FIELD_NAMES[Index];
    Column.Title.Caption := HEADERS[Index];
    Column.Width := WIDTHS[Index];
    Column.ReadOnly := Index = 0;
  end;
  FDBGrid.OnTitleClick := DBTitleClick;
  Identify(FDBGrid, 6110);
  LoadData(nil);
  FSearch.OnChange := SearchChanged;
end;

procedure TComplexControlPages.LoadData(Sender: TObject);
var
  Row, Column: Integer;
begin
  FData.DisableControls;
  try
    FData.Close;
    FData.Filtered := False;
    FData.IndexFieldNames := '';
    FSearch.Text := '';
    FData.CreateDataSet;
    FData.LogChanges := False;
    for Row := 1 to 1000 do
    begin
      FData.Append;
      FData.Fields[0].AsInteger := Row;
      for Column := 1 to 5 do
        FData.Fields[Column].AsString := EmployeeCell(Row, Column);
      FData.Fields[6].AsDateTime := EncodeDate(2024, (Row mod 12) + 1, (Row mod 28) + 1);
      FData.Post;
    end;
    FData.FieldByName('ID').ReadOnly := True;
    FData.First;
  finally
    FData.EnableControls;
  end;
  DataChanged(FData);
end;

procedure TComplexControlPages.DataChanged(DataSet: TDataSet);
begin
  if not FData.Active then Exit;
  if FData.IsEmpty then
    FDBStatus.Caption := 'TDBGrid | 筛选结果 0 条'
  else
    FDBStatus.Caption := Format('TDBGrid | 当前 %d / %d 条 | ID %d | 姓名=%s',
      [FData.RecNo, FData.RecordCount, FData.FieldByName('ID').AsInteger,
       FData.FieldByName('EmployeeName').AsString]);
end;

procedure TComplexControlPages.DataFilter(DataSet: TDataSet; var Accept: Boolean);
var
  Query: string;
begin
  Query := LowerCase(Trim(FSearch.Text));
  Accept := (Query = '') or (Pos(Query, LowerCase(DataSet.FieldByName('EmployeeName').AsString)) > 0)
    or (Pos(Query, LowerCase(DataSet.FieldByName('City').AsString)) > 0)
    or (Pos(Query, LowerCase(DataSet.FieldByName('Email').AsString)) > 0);
end;

procedure TComplexControlPages.SearchChanged(Sender: TObject);
begin
  if not FData.Active then Exit;
  FData.CheckBrowseMode;
  FData.Filtered := False;
  FData.Filtered := Trim(FSearch.Text) <> '';
  FData.First;
  DataChanged(FData);
end;

procedure TComplexControlPages.DBTitleClick(Column: TColumn);
begin
  FData.CheckBrowseMode;
  FData.IndexFieldNames := Column.FieldName;
  FData.First;
  DataChanged(FData);
end;

procedure TComplexControlPages.BuildVirtualTree;
var
  Tab: TTabSheet;
  Toolbar: TPanel;
  Column: TVirtualTreeColumn;
  Index: Integer;
begin
  Tab := NewPage('TVirtualStringTree', 'Virtual TreeView 5.5.3：10 个部门、1000 名员工；展开、勾选、F2 编辑员工姓名。',
    6200, Toolbar, FVirtualStatus);
  AddButton(Toolbar, '全部展开', 12, 6211, 1, VirtualAction);
  AddButton(Toolbar, '全部折叠', 124, 6212, 2, VirtualAction);
  AddButton(Toolbar, '恢复数据', 236, 6213, 3, VirtualAction);
  FVirtualTree := TVirtualStringTree.Create(Tab);
  FVirtualTree.Parent := Tab;
  FVirtualTree.Align := alClient;
  FVirtualTree.AccessibleName := '员工部门虚拟树';
  FVirtualTree.NodeDataSize := SizeOf(TEmployeeNode);
  FVirtualTree.DefaultNodeHeight := 24;
  FVirtualTree.Header.Options := FVirtualTree.Header.Options + [hoVisible, hoColumnResize, hoDrag];
  FVirtualTree.Header.Height := 26;
  for Index := 0 to 6 do
  begin
    Column := FVirtualTree.Header.Columns.Add;
    Column.Text := HEADERS[Index];
    Column.Width := WIDTHS[Index];
  end;
  FVirtualTree.TreeOptions.MiscOptions := FVirtualTree.TreeOptions.MiscOptions + [toCheckSupport, toEditable];
  FVirtualTree.TreeOptions.SelectionOptions := FVirtualTree.TreeOptions.SelectionOptions + [toExtendedFocus];
  FVirtualTree.TreeOptions.PaintOptions := FVirtualTree.TreeOptions.PaintOptions + [toShowHorzGridLines, toShowVertGridLines];
  FVirtualTree.OnInitNode := VirtualInitNode;
  FVirtualTree.OnInitChildren := VirtualInitChildren;
  FVirtualTree.OnGetText := VirtualGetText;
  FVirtualTree.OnNewText := VirtualNewText;
  FVirtualTree.OnEditing := VirtualEditing;
  FVirtualTree.OnChange := VirtualChanged;
  FVirtualTree.OnChecked := VirtualChanged;
  FVirtualTree.OnExpanded := VirtualChanged;
  FVirtualTree.OnCollapsed := VirtualChanged;
  Identify(FVirtualTree, 6210);
  FVirtualTree.RootNodeCount := 10;
  FVirtualStatus.Caption := 'TVirtualStringTree | 10 个部门、1000 名员工 | 双击部门或使用 +/- 展开、折叠';
end;

procedure TComplexControlPages.VirtualInitNode(Sender: TBaseVirtualTree; ParentNode, Node: PVirtualNode;
  var InitialStates: TVirtualNodeInitStates);
var
  Data, ParentData: PEmployeeNode;
begin
  Data := Sender.GetNodeData(Node);
  if ParentNode = nil then
  begin
    Data.EmployeeId := 0;
    Data.Department := Node.Index;
    Include(InitialStates, ivsHasChildren);
  end
  else
  begin
    ParentData := Sender.GetNodeData(ParentNode);
    Data.Department := ParentData.Department;
    Data.EmployeeId := Data.Department * 100 + Integer(Node.Index) + 1;
  end;
  Node.CheckType := ctCheckBox;
end;

procedure TComplexControlPages.VirtualInitChildren(Sender: TBaseVirtualTree; Node: PVirtualNode; var ChildCount: Cardinal);
begin
  if Sender.GetNodeLevel(Node) = 0 then ChildCount := 100 else ChildCount := 0;
end;

procedure TComplexControlPages.VirtualGetText(Sender: TBaseVirtualTree; Node: PVirtualNode;
  Column: TColumnIndex; TextType: TVSTTextType; var CellText: UnicodeString);
var
  Data: PEmployeeNode;
begin
  Data := Sender.GetNodeData(Node);
  CellText := '';
  if Data.EmployeeId = 0 then
  begin
    if Column = 0 then CellText := DEPARTMENTS[Data.Department];
    if Column = 1 then CellText := '100 名员工';
  end
  else if (Column = 1) and (FVirtualNames[Data.EmployeeId] <> '') then
    CellText := FVirtualNames[Data.EmployeeId]
  else
    CellText := EmployeeCell(Data.EmployeeId, Column);
end;

procedure TComplexControlPages.VirtualEditing(Sender: TBaseVirtualTree; Node: PVirtualNode;
  Column: TColumnIndex; var Allowed: Boolean);
var
  Data: PEmployeeNode;
begin
  Data := Sender.GetNodeData(Node);
  Allowed := (Column = 1) and (Data.EmployeeId > 0);
end;

procedure TComplexControlPages.VirtualNewText(Sender: TBaseVirtualTree; Node: PVirtualNode;
  Column: TColumnIndex; NewText: UnicodeString);
var
  Data: PEmployeeNode;
begin
  Data := Sender.GetNodeData(Node);
  if (Column = 1) and (Data.EmployeeId > 0) then
    FVirtualNames[Data.EmployeeId] := NewText;
  VirtualChanged(Sender, Node);
end;

procedure TComplexControlPages.VirtualChanged(Sender: TBaseVirtualTree; Node: PVirtualNode);
var
  Text: UnicodeString;
begin
  if Node = nil then Exit;
  VirtualGetText(Sender, Node, 0, ttNormal, Text);
  FVirtualStatus.Caption := Format('TVirtualStringTree | 10 个部门、1000 名员工 | 节点=%s | 勾选=%s | 展开=%s',
    [Text, BoolToStr(Node.CheckState = csCheckedNormal, True), BoolToStr(Sender.Expanded[Node], True)]);
end;

procedure TComplexControlPages.VirtualAction(Sender: TObject);
var
  Index: Integer;
begin
  case (Sender as TButton).Tag of
    1: FVirtualTree.FullExpand;
    2: FVirtualTree.FullCollapse;
    3:
      begin
        FVirtualTree.CancelEditNode;
        FVirtualTree.Clear;
        for Index := Low(FVirtualNames) to High(FVirtualNames) do FVirtualNames[Index] := '';
        FVirtualTree.RootNodeCount := 10;
      end;
  end;
  FVirtualStatus.Caption := 'TVirtualStringTree | 10 个部门、1000 名员工 | ' + (Sender as TButton).Caption;
end;

procedure TComplexControlPages.BuildDevExpressPages;
var
  Tab: TTabSheet;
  Toolbar: TPanel;
  Status: TStaticText;
  {$IFDEF WITH_DEVEXPRESS}
  Grid: TcxGrid;
  View: TcxGridTableView;
  Tree: TcxTreeList;
  Column: Integer;
  {$ELSE}
  Notice: TStaticText;
  Index: Integer;
  {$ENDIF}
begin
  {$IFDEF WITH_DEVEXPRESS}
  {$IFDEF DEVEXPRESS_TRIAL}
  // DevExpress 26.1 requires an explicit opt-in for its native UIA providers.
  dxUIAutomationEnabled := True;
  {$ENDIF}
  Tab := NewPage('TcxGrid', 'DevExpress TcxGrid：1000 条；支持编辑、列头排序、拖拽分组和筛选。', 6300, Toolbar, Status);
  Grid := TcxGrid.Create(Tab);
  {$IFDEF DEVEXPRESS_TRIAL}
  Grid.Automation.Name := 'TcxGrid 员工表';
  {$ENDIF}
  Grid.Parent := Tab;
  Grid.Align := alClient;
  View := Grid.CreateView(TcxGridTableView) as TcxGridTableView;
  FCxGridView := View;
  FCxGridStatus := Status;
  AddButton(Toolbar, '恢复数据', 12, 6311, 0, LoadCxGridData);
  Grid.Levels.Add.GridView := View;
  for Column := 0 to 6 do
  begin
    with View.CreateColumn do
    begin
      Caption := HEADERS[Column];
      Width := WIDTHS[Column];
      if Column = 0 then DataBinding.ValueType := 'Integer'
      else DataBinding.ValueType := 'String';
      Options.Editing := Column <> 0;
    end;
  end;
  View.OptionsView.GroupByBox := True;
  LoadCxGridData(nil);
  Identify(Grid, 6310);
  Tab := NewPage('TcxTreeList', 'DevExpress TcxTreeList：10 个部门、1000 名员工；可展开、折叠和编辑。', 6400, Toolbar, Status);
  Tree := TcxTreeList.Create(Tab);
  {$IFDEF DEVEXPRESS_TRIAL}
  Tree.Automation.Name := 'TcxTreeList 部门员工树';
  {$ENDIF}
  Tree.Parent := Tab;
  Tree.Align := alClient;
  FCxTreeList := Tree;
  FCxTreeStatus := Status;
  AddButton(Toolbar, '全部展开', 12, 6411, 1, CxTreeAction);
  AddButton(Toolbar, '全部折叠', 124, 6412, 2, CxTreeAction);
  AddButton(Toolbar, '恢复数据', 236, 6413, 3, CxTreeAction);
  for Column := 0 to 6 do
    with Tree.CreateColumn do
    begin
      Caption.Text := HEADERS[Column];
      Width := WIDTHS[Column];
      Options.Editing := Column <> 0;
    end;
  LoadCxTreeData;
  Identify(Tree, 6410);
  {$ELSE}
  for Index := 0 to 1 do
  begin
    if Index = 0 then
      Tab := NewPage('TcxGrid（待接入）', 'DevExpress 控件尚未接入。', 6300, Toolbar, Status)
    else
      Tab := NewPage('TcxTreeList（待接入）', 'DevExpress 控件尚未接入。', 6400, Toolbar, Status);
    Notice := TStaticText.Create(Tab);
    Notice.Parent := Tab;
    Notice.SetBounds(24, 32, 900, 140);
    Notice.AutoSize := False;
    Notice.Caption := '此版本未包含 DevExpress 控件。' + #13#10 + #13#10 +
      '需要与编译器版本匹配的 DevExpress VCL 库，接入后重新构建。' + #13#10 +
      'TStringGrid、TDBGrid 和 TVirtualStringTree 页签可直接使用。';
    Identify(Notice, 6310 + Index * 100);
    Status.Caption := '尚未接入 | 当前页面没有创建 DevExpress 控件';
  end;
  {$ENDIF}
end;

{$IFDEF WITH_DEVEXPRESS}
procedure TComplexControlPages.LoadCxGridData(Sender: TObject);
var
  Row, Column: Integer;
begin
  FCxGridView.DataController.BeginUpdate;
  try
    FCxGridView.DataController.RecordCount := 0;
    FCxGridView.DataController.RecordCount := 1000;
    for Row := 1 to 1000 do
    begin
      FCxGridView.DataController.Values[Row - 1, 0] := Row;
      for Column := 1 to 6 do
        FCxGridView.DataController.Values[Row - 1, Column] := EmployeeCell(Row, Column);
    end;
  finally
    FCxGridView.DataController.EndUpdate;
  end;
  FCxGridStatus.Caption := 'TcxGrid | 1000 条、7 列 | ID 按数值排序 | 数据修改仅保存在内存';
  {$IFDEF DEVEXPRESS_TRIAL}
  FCxGridStatus.Caption := FCxGridStatus.Caption + ' | DevExpress 试用评估版';
  {$ENDIF}
end;

procedure TComplexControlPages.LoadCxTreeData;
var
  ParentNode, Node: TcxTreeListNode;
  Department, Row, Column: Integer;
begin
  FCxTreeList.BeginUpdate;
  try
    FCxTreeList.Clear;
    for Department := 0 to 9 do
    begin
      ParentNode := FCxTreeList.Add;
      ParentNode.Values[0] := DEPARTMENTS[Department];
      ParentNode.Values[1] := '100 名员工';
      for Row := 1 to 100 do
      begin
        Node := ParentNode.AddChild;
        for Column := 0 to 6 do
          Node.Values[Column] := EmployeeCell(Department * 100 + Row, Column);
      end;
    end;
  finally
    FCxTreeList.EndUpdate;
  end;
  FCxTreeList.FullCollapse;
  FCxTreeStatus.Caption := 'TcxTreeList | 10 个部门、1000 名员工 | 数据修改仅保存在内存';
  {$IFDEF DEVEXPRESS_TRIAL}
  FCxTreeStatus.Caption := FCxTreeStatus.Caption + ' | DevExpress 试用评估版';
  {$ENDIF}
end;

procedure TComplexControlPages.CxTreeAction(Sender: TObject);
begin
  case (Sender as TButton).Tag of
    1: FCxTreeList.FullExpand;
    2: FCxTreeList.FullCollapse;
    3: LoadCxTreeData;
  end;
end;
{$ENDIF}

end.
