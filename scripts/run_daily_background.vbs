' Silent Background Launcher for Daily AI Reel Generator
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
RootDir = FSO.GetParentFolderName(ScriptDir)

WshShell.CurrentDirectory = RootDir
WshShell.Run "python -c ""from core.scheduler import ReelScheduler; s = ReelScheduler(); s.run_daily_job()""", 0, True
Set WshShell = Nothing
