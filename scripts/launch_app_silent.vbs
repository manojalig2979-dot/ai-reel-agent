' Silent Web Dashboard Launcher (No Black Terminal Window)
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
RootDir = FSO.GetParentFolderName(ScriptDir)

WshShell.CurrentDirectory = RootDir

' Launch Streamlit silently in the background (0 = Hidden window)
WshShell.Run "python -m streamlit run app.py --server.headless false", 0, False

Set WshShell = Nothing
