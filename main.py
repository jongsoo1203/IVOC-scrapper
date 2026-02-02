import tkinter as tk
from tools.gui import ScraperGUI


def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
