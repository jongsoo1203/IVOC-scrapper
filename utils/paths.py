import os
from pathlib import Path


def ensure_data_dir(project_root: str) -> str:
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_project_root() -> str:
    # when running python main.py from scraper_app/
    return os.getcwd()


def get_downloads_folder() -> str:
    """Same logic as your original code."""
    if os.name == "nt":
        import winreg
        sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    return str(Path.home() / "Downloads")


def data_path(filename: str) -> str:
    root = get_project_root()
    data_dir = ensure_data_dir(root)
    return os.path.join(data_dir, filename)
