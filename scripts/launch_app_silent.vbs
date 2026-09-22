' Silent Desktop App Window Launcher (Dedicated Native Window Frame)
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
RootDir = FSO.GetParentFolderName(ScriptDir)

WshShell.CurrentDirectory = RootDir

' Launch dedicated desktop window via launch_desktop_app.py (0 = Hidden console window)
WshShell.Run "python scripts\launch_desktop_app.py", 0, False

Set WshShell = Nothing
