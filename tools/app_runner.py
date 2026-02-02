from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

from utils.config import REDDIT_SUBS, US_LINKS, load_config
from tools.emailer import Emailer
from tools.reddit_scraper import RedditScraper
from tools.report_writer import ReportWriter
from tools.uscommunity_scraper import USCommunityScraper

ProgressCb = Callable[[int, int, str], None]
log = logging.getLogger("tools.runner")


def run_scrape(
    us_start: datetime,
    us_end: datetime,
    reddit_start: datetime,
    reddit_end: datetime,
    keywords: list[str],
    time_bucket: str,
    progress_callback: Optional[ProgressCb] = None,
) -> Path:
    load_dotenv()
    cfg = load_config()

    # Fail fast for missing Reddit creds
    if not (cfg.reddit.client_id and cfg.reddit.client_secret):
        raise RuntimeError("Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")

    us = USCommunityScraper.create()
    reddit = RedditScraper(cfg)
    writer = ReportWriter(cfg.data_dir)

    total = len(US_LINKS) + len(REDDIT_SUBS)
    done = 0
    rows: list[list[str]] = []

    for link in US_LINKS:
        done += 1
        progress_callback and progress_callback(done, total, f"US Community ({done}/{len(US_LINKS)})")
        rows.extend(us.scrape_board(link, us_start, us_end, keywords, max_pages=cfg.max_pages_uscommunity))

    for sub in REDDIT_SUBS:
        done += 1
        progress_callback and progress_callback(done, total, f"Reddit r/{sub} ({done-len(US_LINKS)}/{len(REDDIT_SUBS)})")
        rows.extend(reddit.scrape(sub, reddit_start, reddit_end, keywords))

    now = datetime.now()
    csv_name = f"{now:%m_%d_%y}_{time_bucket}.csv"
    csv_path = writer.write_csv(rows, csv_name)

    progress_callback and progress_callback(total, total, "Formatting XLSX")
    xlsx_path = writer.csv_to_styled_xlsx(csv_path)

    # Optional email if configured
    if cfg.email.user and cfg.email.password:
        Emailer(cfg.email.smtp_host, cfg.email.smtp_port, cfg.email.user, cfg.email.password).send_with_attachment(
            recipient=cfg.email.user,
            subject=xlsx_path.name,
            body="",
            attachment_path=xlsx_path,
        )

    return xlsx_path
