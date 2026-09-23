import os
import sys
import time
import socket
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PORT = 8501
URL = f"http://127.0.0.1:{PORT}"
SPLASH_PATH = (BASE_DIR / "assets" / "splash.html").resolve()


def is_server_running(port: int = PORT) -> bool:
    """Fast non-blocking socket check to see if Streamlit server is already responding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.08)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_streamlit_server():
    """Starts Streamlit in the background with maximum startup optimization flags."""
    if is_server_running():
        return

    python_exe = sys.executable
    cmd = [
        python_exe,
        "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--server.address", "127.0.0.1",
        "--server.fileWatcherType", "none",
        "--global.developmentMode", "false",
        "--browser.gatherUsageStats", "false",
        "--client.toolbarMode", "viewer",
        "--theme.base", "dark"
    ]

    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True
    )


def find_browser_app_mode_exe() -> str:
    """Finds Microsoft Edge or Google Chrome to run in dedicated standalone app-window mode."""
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return ""


def launch_desktop_window():
    """Launches the dedicated standalone Desktop App Window with instant visual feedback."""
    already_running = is_server_running()
    
    if not already_running:
        start_streamlit_server()
        # If server wasn't running, target the animated instant splash loader
        target_url = SPLASH_PATH.as_uri() if SPLASH_PATH.exists() else URL
    else:
        target_url = URL

    browser_exe = find_browser_app_mode_exe()

    if browser_exe:
        app_args = [
            browser_exe,
            f"--app={target_url}",
            "--window-size=1380,880",
            "--window-position=80,60",
            "--app-id=NDReelStudio"
        ]
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(app_args, creationflags=CREATE_NO_WINDOW)
    else:
        import webbrowser
        webbrowser.open(target_url)


if __name__ == "__main__":
    launch_desktop_window()
