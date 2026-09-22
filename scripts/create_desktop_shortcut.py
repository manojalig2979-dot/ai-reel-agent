import os
import sys
from pathlib import Path
import subprocess

def create_shortcut():
    # Detect all active desktop locations (including OneDrive sync folders)
    desktops = set()
    
    # 1. Official Windows Shell Desktop Special Folder
    try:
        ps_desktop_cmd = ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"]
        res = subprocess.run(ps_desktop_cmd, capture_output=True, text=True, check=False)
        p = res.stdout.strip()
        if p and Path(p).exists():
            desktops.add(Path(p))
    except Exception:
        pass

    # 2. UserProfile Desktop and OneDrive Desktop
    userprofile = Path(os.environ.get("USERPROFILE", "C:/Users/manoj"))
    for candidate in [
        userprofile / "OneDrive" / "Desktop",
        userprofile / "Desktop",
        Path("C:/Users/Public/Desktop")
    ]:
        if candidate.exists():
            desktops.add(candidate)

    base_dir = Path(__file__).resolve().parent.parent
    target_vbs = (base_dir / "scripts" / "launch_app_silent.vbs").resolve()
    icon_path = (base_dir / "assets" / "nd_reel.ico").resolve()

    for desktop in desktops:
        shortcut_path = (desktop / "ND Reel Studio.lnk").resolve()
        ps_cmd = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path.as_posix()}')
        $Shortcut.TargetPath = 'wscript.exe'
        $Shortcut.Arguments = '"{target_vbs.as_posix()}"'
        $Shortcut.WorkingDirectory = '{base_dir.as_posix()}'
        $Shortcut.Description = 'ND Reel AI Studio & Auto-Publisher'
        if (Test-Path '{icon_path.as_posix()}') {{
            $Shortcut.IconLocation = '{icon_path.as_posix()}'
        }}
        $Shortcut.Save()
        """
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[SUCCESS] Desktop shortcut created at: {shortcut_path}")
        except Exception:
            pass


if __name__ == "__main__":
    create_shortcut()
