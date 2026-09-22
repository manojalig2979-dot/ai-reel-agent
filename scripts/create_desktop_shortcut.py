import os
import sys
from pathlib import Path

def create_shortcut():
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        pass

    # Windows Desktop Path
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut_path = desktop / "ND Reel Studio.lnk"

    base_dir = Path(__file__).resolve().parent.parent
    target_bat = base_dir / "scripts" / "launch_web_dashboard.bat"
    icon_path = base_dir / "assets" / "nd_reel.ico"

    # Use PowerShell to create the shortcut reliably
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = '{target_bat}'
    $Shortcut.WorkingDirectory = '{base_dir}'
    $Shortcut.Description = 'ND Reel AI Studio & Auto-Publisher'
    if (Test-Path '{icon_path}') {{
        $Shortcut.IconLocation = '{icon_path}'
    }}
    $Shortcut.Save()
    """

    import subprocess
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Desktop shortcut created at: {shortcut_path}")


if __name__ == "__main__":
    create_shortcut()
