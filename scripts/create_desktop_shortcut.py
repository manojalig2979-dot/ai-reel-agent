import os
import sys
from pathlib import Path
import subprocess

def create_shortcut():
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut_path = desktop / "ND Reel Studio.lnk"

    base_dir = Path(__file__).resolve().parent.parent
    target_vbs = base_dir / "scripts" / "launch_app_silent.vbs"
    icon_path = base_dir / "assets" / "nd_reel.ico"

    # Use wscript.exe to run VBScript silently with custom icon
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = 'wscript.exe'
    $Shortcut.Arguments = '"{target_vbs}"'
    $Shortcut.WorkingDirectory = '{base_dir}'
    $Shortcut.Description = 'ND Reel AI Studio & Auto-Publisher'
    if (Test-Path '{icon_path}') {{
        $Shortcut.IconLocation = '{icon_path}'
    }}
    $Shortcut.Save()
    """

    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Silent Desktop shortcut created at: {shortcut_path}")


if __name__ == "__main__":
    create_shortcut()
