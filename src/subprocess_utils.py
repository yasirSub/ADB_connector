import subprocess
import sys
import os
from typing import Any, Dict, List, Optional


def _no_window_startupinfo():
    """Create startupinfo to hide console windows on Windows."""
    if os.name != 'nt':
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def run_no_window(args: List[str], **kwargs) -> subprocess.CompletedProcess:
    """subprocess.run wrapper that prevents opening console windows on Windows."""
    if os.name == 'nt':
        kwargs.setdefault('startupinfo', _no_window_startupinfo())
        # Avoid creating a new console window
        kwargs.setdefault('creationflags', 0x08000000)  # CREATE_NO_WINDOW
    # Sensible defaults
    kwargs.setdefault('shell', False)
    return subprocess.run(args, **kwargs)


