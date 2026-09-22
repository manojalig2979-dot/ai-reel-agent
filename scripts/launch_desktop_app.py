import os
import sys
import time
import socket
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PORT = 8501
URL = f"http://127.0.0.1:{PORT}"

def is_server_running(port: int = PORT) -> bool:
    """Check if the Streamlit server is already responding."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        pass
    
    # Fallback socket check
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_streamlit_server():
    """Starts Streamlit in the background without any console window."""
    if is_server_running():
        return

    python_exe = sys.executable
    cmd = [
        python_exe,
        "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark"
    ]

    # Windows flags to completely hide console window
    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True
    )

    # Wait for server to become ready
    for _ in range(35):
        time.sleep(0.3)
        if is_server_running():
            break


def find_browser_app_mode_exe() -> str:
    """Finds Edge or Chrome to run in standalone desktop application window mode."""
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
    """Launches the dedicated standalone Desktop App Window."""
    start_streamlit_server()
    browser_exe = find_browser_app_mode_exe()

    if browser_exe:
        # Launch dedicated frameless/app-mode window without browser tabs or URL bar
        app_args = [
            browser_exe,
            f"--app={URL}",
            "--window-size=1380,880",
            "--window-position=80,60",
            "--app-id=NDReelStudio"
        ]
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(app_args, creationflags=CREATE_NO_WINDOW)
    else:
        import webbrowser
        webbrowser.open(URL)


if __name__ == "__main__":
    launch_desktop_window()
