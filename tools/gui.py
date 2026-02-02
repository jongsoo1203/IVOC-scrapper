import datetime as dt
import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

import pandas as pd
from tkcalendar import DateEntry

from utils.config import REDDIT_LINKS, US_LINKS, get_reddit_config, get_smtp_config
from utils.paths import data_path, get_downloads_folder
from tools.reddit_scraper import reddit_scraper_historical
from tools.uscommunity_scraper import us_community_deep_scrape
from tools.report_writer import sort_csv_to_xlsx
from tools.emailer import send_email


def _now_parts():
    local_time = time.localtime()
    return local_time.tm_mon, local_time.tm_mday, local_time.tm_year


def parse_manual_timestamp(text: str) -> dt.datetime:
    """
    Manual Timestamp Mode expects: MM/DD/YY HH:MM
    Example: 01/31/26 09:30
    """
    text = (text or "").strip()
    return dt.datetime.strptime(text, "%m/%d/%y %H:%M")


def uscomm_reddit_pull(
    us_start,
    us_end,
    reddit_start,
    reddit_end,
    keywords,
    csv_path,
    progress_callback=None
):
    total_sources = len(US_LINKS) + len(REDDIT_LINKS)
    current = 0

    # US Community
    try:
        for link in US_LINKS:
            current += 1
            if progress_callback:
                progress_callback(current, total_sources, f"Processing US Community ({current}/{len(US_LINKS)})")
            us_community_deep_scrape(link, us_start, us_end, keywords, csv_path, max_pages=10, progress_callback=progress_callback)
    except Exception as e:
        print(e)

    # Reddit
    try:
        reddit_cfg = get_reddit_config()
        for sub in REDDIT_LINKS:
            current += 1
            if progress_callback:
                progress_callback(current, total_sources, f"Processing Reddit r/{sub} ({current - len(US_LINKS)}/{len(REDDIT_LINKS)})")
            reddit_scraper_historical(reddit_cfg, sub, reddit_start, reddit_end, keywords, csv_path, progress_callback)
    except Exception as e:
        print("Reddit pull failed:", repr(e))

    if progress_callback:
        progress_callback(total_sources, total_sources, "Sorting and formatting...")

    xlsx_path = sort_csv_to_xlsx(csv_path)

    # Copy to Downloads (same as original behavior)
    if progress_callback:
        progress_callback(total_sources, total_sources, "Saving to Downloads...")

    try:
        downloads_path = get_downloads_folder()
        destination = os.path.join(downloads_path, os.path.basename(xlsx_path))
        shutil.copy2(xlsx_path, destination)
        print(f"File saved to Downloads: {destination}")
    except Exception as e:
        print(f"Failed to save to Downloads: {e}")

    if progress_callback:
        progress_callback(total_sources, total_sources, "Sending email...")

    # Email
    try:
        smtp_cfg = get_smtp_config()
        send_email(smtp_cfg, subject=os.path.basename(xlsx_path), body="", file_path=xlsx_path)
    except Exception as e:
        print("Email failed:", repr(e))

    return xlsx_path


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper")
        self.root.geometry("750x900")
        self.root.configure(bg="#f5f5f5")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabelframe", background="#f5f5f5", borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background="#f5f5f5", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 9))
        style.configure("TRadiobutton", background="#f5f5f5", font=("Segoe UI", 9))
        style.configure("TCheckbutton", background="#f5f5f5", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9))

        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)

        title = tk.Label(main_frame, text="Web Scraper",
                         font=("Segoe UI", 18, "bold"), bg="#f5f5f5", fg="#1a1a1a")
        title.pack(pady=(0, 20))

        mode_frame = ttk.LabelFrame(main_frame, text="Select Mode", padding=15)
        mode_frame.pack(fill="x", pady=(0, 10))

        self.mode_var = tk.StringVar(value="file")
        ttk.Radiobutton(mode_frame, text="Load from Previous File", variable=self.mode_var,
                        value="file", command=self.toggle_mode).pack(anchor="w", pady=3)
        ttk.Radiobutton(mode_frame, text="Manual Timestamps", variable=self.mode_var,
                        value="timestamp", command=self.toggle_mode).pack(anchor="w", pady=3)
        ttk.Radiobutton(mode_frame, text="Date Range", variable=self.mode_var,
                        value="daterange", command=self.toggle_mode).pack(anchor="w", pady=3)

        # --- File mode
        self.file_frame = ttk.LabelFrame(main_frame, text="Previous File Mode", padding=15)
        self.file_frame.pack(fill="x", pady=(0, 10))

        file_grid = ttk.Frame(self.file_frame)
        file_grid.pack(fill="x")

        ttk.Label(file_grid, text="Previous File Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.file_date_entry = DateEntry(file_grid, width=25, font=("Segoe UI", 9))
        self.file_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(file_grid, text="Time of Day:").grid(row=1, column=0, sticky="w", pady=5)
        self.file_time_var = tk.StringVar(value="morning")
        time_frame_file = ttk.Frame(file_grid)
        time_frame_file.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        ttk.Radiobutton(time_frame_file, text="Morning", variable=self.file_time_var, value="morning").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(time_frame_file, text="Afternoon", variable=self.file_time_var, value="afternoon").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(time_frame_file, text="Evening", variable=self.file_time_var, value="evening").pack(side=tk.LEFT, padx=5)

        browse_btn = ttk.Button(self.file_frame, text="Browse for File...", command=self.browse_file)
        browse_btn.pack(pady=10)

        self.file_info_label = ttk.Label(self.file_frame, text="No file loaded", foreground="gray")
        self.file_info_label.pack(pady=5)

        self.loaded_file_path = None

        # --- Timestamp mode
        self.timestamp_frame = ttk.LabelFrame(main_frame, text="Manual Timestamp Mode", padding=15)
        self.timestamp_frame.pack(fill="x", pady=(0, 10))

        ts_grid = ttk.Frame(self.timestamp_frame)
        ts_grid.pack(fill="x")

        ttk.Label(ts_grid, text="US Community:").grid(row=0, column=0, sticky="w", pady=5)
        self.us_timestamp_entry = ttk.Entry(ts_grid, width=25, font=("Segoe UI", 9))
        self.us_timestamp_entry.grid(row=0, column=1, padx=10, pady=5)
        self.us_timestamp_entry.insert(0, "MM/DD/YY HH:MM")

        ttk.Label(ts_grid, text="Reddit:").grid(row=1, column=0, sticky="w", pady=5)
        self.reddit_timestamp_entry = ttk.Entry(ts_grid, width=25, font=("Segoe UI", 9))
        self.reddit_timestamp_entry.grid(row=1, column=1, padx=10, pady=5)
        self.reddit_timestamp_entry.insert(0, "MM/DD/YY HH:MM")

        # --- Date range mode
        self.daterange_frame = ttk.LabelFrame(main_frame, text="Date Range Mode", padding=15)
        self.daterange_frame.pack(fill="x", pady=(0, 10))

        dr_grid = ttk.Frame(self.daterange_frame)
        dr_grid.pack(fill="x")

        ttk.Label(dr_grid, text="Start Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_date_entry = DateEntry(dr_grid, width=25, font=("Segoe UI", 9))
        self.start_date_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dr_grid, text="End Date:").grid(row=1, column=0, sticky="w", pady=5)
        self.end_date_entry = DateEntry(dr_grid, width=25, font=("Segoe UI", 9))
        self.end_date_entry.grid(row=1, column=1, padx=10, pady=5)

        self.use_end_date_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.daterange_frame, text="Use end date (uncheck for today)",
                        variable=self.use_end_date_var).pack(anchor="w", pady=5)

        # --- Keywords
        keyword_frame = ttk.LabelFrame(main_frame, text="Keyword Filter (Optional)", padding=15)
        keyword_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(keyword_frame, text="Keywords (comma-separated):").pack(anchor="w")
        self.keyword_entry = ttk.Entry(keyword_frame, width=55, font=("Segoe UI", 9))
        self.keyword_entry.pack(fill="x", pady=5)
        ttk.Label(keyword_frame, text="e.g., S25, fold, camera issue",
                  font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

        # --- Output time label
        time_frame = ttk.LabelFrame(main_frame, text="Output File Time", padding=15)
        time_frame.pack(fill="x", pady=(0, 10))

        self.time_var = tk.StringVar(value="morning")
        time_btns = ttk.Frame(time_frame)
        time_btns.pack()
        ttk.Radiobutton(time_btns, text="Morning", variable=self.time_var, value="morning").pack(side="left", padx=20)
        ttk.Radiobutton(time_btns, text="Afternoon", variable=self.time_var, value="afternoon").pack(side="left", padx=20)
        ttk.Radiobutton(time_btns, text="Evening", variable=self.time_var, value="evening").pack(side="left", padx=20)

        # --- Progress
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=15)
        self.progress_frame.pack(fill="x", pady=(0, 10))

        self.progress_bar = ttk.Progressbar(self.progress_frame, length=600, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)

        self.progress_label = ttk.Label(self.progress_frame, text="Ready to start scraping")
        self.progress_label.pack(pady=5)

        self.status_detail_label = ttk.Label(self.progress_frame, text="", font=("Segoe UI", 8), foreground="#666")
        self.status_detail_label.pack(pady=2)

        self.start_button = ttk.Button(main_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.pack(pady=15)

        self.toggle_mode()

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Previous CSV File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.loaded_file_path = filename
            self.file_info_label.config(text=f"Loaded: {os.path.basename(filename)}", foreground="green")

    def toggle_mode(self):
        self.file_frame.pack_forget()
        self.timestamp_frame.pack_forget()
        self.daterange_frame.pack_forget()

        if self.mode_var.get() == "file":
            self.file_frame.pack(fill="x", pady=(0, 10))
        elif self.mode_var.get() == "timestamp":
            self.timestamp_frame.pack(fill="x", pady=(0, 10))
        else:
            self.daterange_frame.pack(fill="x", pady=(0, 10))

    def update_progress(self, current, total, message, detail=""):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current
        self.progress_label.config(text=message)
        self.status_detail_label.config(text=detail)

        if total > 0:
            pct = int((current / total) * 100)
            self.progress_label.config(text=f"{message} ({pct}%)")

        self.root.update_idletasks()

    def start_scraping(self):
        def scrape_thread():
            try:
                self.root.after(0, lambda: self.start_button.config(state="disabled"))
                self.root.after(0, lambda: self.update_progress(0, 100, "Initializing...", "Preparing to scrape data"))

                keywords = [k.strip() for k in self.keyword_entry.get().split(",") if k.strip()]

                mon, day, yr = _now_parts()
                csv_name = f"{mon}_{day}_{yr % 100}_{self.time_var.get()}.csv"
                csv_path = data_path(csv_name)

                if self.mode_var.get() == "file":
                    if self.loaded_file_path:
                        file_path = self.loaded_file_path
                    else:
                        file_date = self.file_date_entry.get_date()
                        file_time = self.file_time_var.get()
                        filename = f"{file_date.month}_{file_date.day}_{file_date.year % 100}_{file_time}.csv"
                        file_path = data_path(filename)

                    if not os.path.exists(file_path):
                        self.root.after(0, lambda: self.start_button.config(state="normal"))
                        self.root.after(0, lambda: messagebox.showerror("Error", f"File not found: {os.path.basename(file_path)}"))
                        return

                    self.root.after(0, lambda: self.update_progress(10, 100, "Reading previous file...", f"Loading {os.path.basename(file_path)}"))

                    df = pd.read_csv(file_path, header=None, parse_dates=[0])
                    last_timestamps = df.groupby(1)[0].max()
                    last_us = last_timestamps.get("uscommunity", None)
                    last_reddit = last_timestamps.get("reddit", None)

                    if last_us is None or last_reddit is None:
                        self.root.after(0, lambda: self.start_button.config(state="normal"))
                        self.root.after(0, lambda: messagebox.showerror("Error", "Could not find timestamps in file"))
                        return

                    last_us = datetime.strptime(str(last_us), "%Y-%m-%d %H:%M:%S")
                    last_reddit = datetime.strptime(str(last_reddit), "%Y-%m-%d %H:%M:%S")
                    end_date = dt.datetime.now()

                    self.root.after(0, lambda: messagebox.showinfo("Info", f"Starting from:\nUS Community: {last_us}\nReddit: {last_reddit}"))

                    uscomm_reddit_pull(
                        last_us, end_date,
                        last_reddit, end_date,
                        keywords, csv_path,
                        lambda c, t, m: self.root.after(0, lambda: self.update_progress(c, t, m, f"Processing {c} of {t} sources"))
                    )

                elif self.mode_var.get() == "timestamp":
                    self.root.after(0, lambda: self.update_progress(10, 100, "Parsing timestamps...", "Reading manual timestamp input"))

                    try:
                        us_ts = parse_manual_timestamp(self.us_timestamp_entry.get())
                        reddit_ts = parse_manual_timestamp(self.reddit_timestamp_entry.get())
                    except Exception:
                        self.root.after(0, lambda: self.start_button.config(state="normal"))
                        self.root.after(0, lambda: messagebox.showerror("Error", "Invalid timestamp format.\nUse: MM/DD/YY HH:MM\nExample: 01/31/26 09:30"))
                        return

                    end_date = dt.datetime.now()

                    uscomm_reddit_pull(
                        us_ts, end_date,
                        reddit_ts, end_date,
                        keywords, csv_path,
                        lambda c, t, m: self.root.after(0, lambda: self.update_progress(c, t, m, f"Processing {c} of {t} sources"))
                    )

                else:
                    self.root.after(0, lambda: self.update_progress(10, 100, "Setting date range...", "Configuring date parameters"))

                    start_date = self.start_date_entry.get_date()
                    if self.use_end_date_var.get():
                        end_date = self.end_date_entry.get_date()
                    else:
                        end_date = dt.datetime.now().date()

                    start_dt = dt.datetime.combine(start_date, dt.time.min)
                    end_dt = dt.datetime.combine(end_date, dt.time.max)

                    uscomm_reddit_pull(
                        start_dt, end_dt,
                        start_dt, end_dt,
                        keywords, csv_path,
                        lambda c, t, m: self.root.after(0, lambda: self.update_progress(c, t, m, f"Processing {c} of {t} sources"))
                    )

                self.root.after(0, lambda: self.update_progress(100, 100, "Complete!", "Scraping finished successfully"))
                self.root.after(0, lambda: self.start_button.config(state="normal"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Scraping completed! File saved to Downloads and email sent."))

            except Exception as e:
                self.root.after(0, lambda: self.update_progress(0, 100, "Error occurred", str(e)))
                self.root.after(0, lambda: self.start_button.config(state="normal"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))

        thread = threading.Thread(target=scrape_thread, daemon=True)
        thread.start()
