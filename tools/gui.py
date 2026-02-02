from __future__ import annotations

import threading
from datetime import datetime, time as dtime
import tkinter as tk
from tkinter import messagebox, ttk

from tkcalendar import DateEntry

from utils.keywords import parse_keywords
from tools.app_runner import run_scrape


class ScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Web Scraper")
        self.root.geometry("750x520")

        self.time_var = tk.StringVar(value="morning")
        self.use_end_date_var = tk.BooleanVar(value=True)

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Web Scraper", font=("Segoe UI", 18, "bold")).pack(pady=(0, 12))

        # Date range
        dr = ttk.LabelFrame(main, text="Date Range", padding=10)
        dr.pack(fill="x", pady=8)

        ttk.Label(dr, text="Start:").grid(row=0, column=0, sticky="w")
        self.start_date = DateEntry(dr, width=20)
        self.start_date.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(dr, text="End:").grid(row=1, column=0, sticky="w")
        self.end_date = DateEntry(dr, width=20)
        self.end_date.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Checkbutton(dr, text="Use end date (uncheck = today now)", variable=self.use_end_date_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4
        )

        # Keywords
        kw = ttk.LabelFrame(main, text="Keywords (comma-separated, optional)", padding=10)
        kw.pack(fill="x", pady=8)
        self.keyword_entry = ttk.Entry(kw)
        self.keyword_entry.pack(fill="x", pady=4)

        # Time bucket
        tb = ttk.LabelFrame(main, text="Output File Time Bucket", padding=10)
        tb.pack(fill="x", pady=8)
        row = ttk.Frame(tb)
        row.pack()
        ttk.Radiobutton(row, text="Morning", variable=self.time_var, value="morning").pack(side="left", padx=12)
        ttk.Radiobutton(row, text="Afternoon", variable=self.time_var, value="afternoon").pack(side="left", padx=12)
        ttk.Radiobutton(row, text="Evening", variable=self.time_var, value="evening").pack(side="left", padx=12)

        # Progress
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill="x", pady=(12, 4))
        self.progress_label = ttk.Label(main, text="Ready")
        self.progress_label.pack()

        # Start
        self.start_button = ttk.Button(main, text="Start", command=self.start_scraping)
        self.start_button.pack(pady=12)

    def update_progress(self, current: int, total: int, message: str) -> None:
        self.progress["maximum"] = total
        self.progress["value"] = current
        pct = int(current / total * 100) if total else 0
        self.progress_label.config(text=f"{message} ({pct}%)")
        self.root.update_idletasks()

    def start_scraping(self) -> None:
        def worker():
            try:
                self.root.after(0, lambda: self.start_button.config(state="disabled"))
                keywords = parse_keywords(self.keyword_entry.get())

                start = datetime.combine(self.start_date.get_date(), dtime.min)
                end = (
                    datetime.combine(self.end_date.get_date(), dtime.max)
                    if self.use_end_date_var.get()
                    else datetime.now()
                )

                out = run_scrape(
                    us_start=start,
                    us_end=end,
                    reddit_start=start,
                    reddit_end=end,
                    keywords=keywords,
                    time_bucket=self.time_var.get(),
                    progress_callback=lambda c, t, m: self.root.after(
                        0, lambda: self.update_progress(c, t, m)
                    ),
                )

                self.root.after(0, lambda: messagebox.showinfo("Done", f"Saved:\n{out}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.start_button.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()
