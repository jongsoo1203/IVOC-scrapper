from __future__ import annotations

import tkinter as tk

from tools.gui import ScraperGUI
from utils.logging_config import setup_logging


def main() -> None:
    setup_logging()
    root = tk.Tk()
    ScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
