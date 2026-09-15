program Win32VclShootingRange;

uses
  Forms,
  MainForm in 'MainForm.pas';

begin
  Application.Initialize;
  Application.MainFormOnTaskbar := True;
  Application.Title := 'Delphi VCL UIA Shooting Range';
  Application.CreateForm(TMainForm, MainForm);
  Application.Run;
end.
