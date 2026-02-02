from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from utils.http import create_fast_session
from utils.keywords import matches_keywords

log = logging.getLogger("tools.uscommunity")


@dataclass
class USCommunityScraper:
    DATE_RE = re.compile(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)")

    def __post_init__(self) -> None:
        self.session = create_fast_session()

    @classmethod
    def create(cls) -> "USCommunityScraper":
        return cls()

    def scrape_board(self, board_url: str, start: datetime, end: datetime, keywords: list[str], max_pages: int) -> list[list[str]]:
        links = self._collect_links(board_url, start, max_pages=max_pages)
        rows: list[list[str]] = []
        for link in links:
            row = self._fetch_post(link, start, end, keywords)
            if row:
                rows.append(row)
        return rows

    def _collect_links(self, board_url: str, start: datetime, max_pages: int) -> list[str]:
        all_links: set[str] = set()

        for page in range(1, max_pages + 1):
            url = f"{board_url}?page={page}" if page > 1 else board_url
            try:
                r = self.session.get(url, timeout=10)
                soup = BeautifulSoup(r.content, "lxml")

                urls = soup.find_all("h3")
                found = re.findall(r"http[s]?://[^\s\"'>]+", str(urls))
                if not found:
                    break

                all_links.update(found)

                # Early stop if we reached older pages
                if page > 1:
                    sample = self._quick_extract_date(found[0])
                    if sample and sample < start:
                        break

                if not soup.find("a", {"rel": "next"}):
                    break

            except Exception as e:
                log.debug("Error collecting links on page %s: %s", page, e)
                break

        return sorted(all_links)

    def _quick_extract_date(self, link: str) -> Optional[datetime]:
        try:
            r = self.session.get(link, timeout=5)
            soup = BeautifulSoup(r.content, "lxml")

            lfd = soup.find(class_="local-friendly-date")
            asd = soup.find(class_="DateTime lia-message-posted-on lia-component-common-widget-date")
            src = lfd["title"] if (lfd and lfd.has_attr("title")) else str(asd)

            m = self.DATE_RE.search(src or "")
            if not m:
                return None

            return datetime.strptime(
                f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}",
                "%m-%d-%Y %I:%M %p",
            )
        except Exception:
            return None

    def _fetch_post(self, link: str, start: datetime, end: datetime, keywords: list[str]) -> Optional[list[str]]:
        try:
            r = self.session.get(link, timeout=8)
            soup = BeautifulSoup(r.content, "lxml")

            asd = soup.find(class_="DateTime lia-message-posted-on lia-component-common-widget-date")
            lfd = soup.find(class_="local-friendly-date")
            src = lfd["title"] if (lfd and lfd.has_attr("title")) else str(asd)

            m = self.DATE_RE.search(src or "")
            if not m:
                return None

            post_time = datetime.strptime(
                f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}",
                "%m-%d-%Y %I:%M %p",
            )
            if not (start <= post_time <= end):
                return None

            title_tag = soup.find("h2") or soup.find("h1") or soup.find("meta", {"property": "og:title"})
            title = (
                title_tag.get_text()
                if hasattr(title_tag, "get_text")
                else title_tag.get("content", "")
                if title_tag
                else ""
            ).strip()

            replies = soup.find_all("div", {"class": "lia-message-body-content"})[:8]
            comments: list[str] = []
            for idx, rep in enumerate(replies, 1):
                rep_text = rep.get_text(" ").replace("\t", " ").replace("\n", " ")
                rep_text = re.sub(r"[\u200e\u200f]", "", rep_text)
                rep_text = re.sub(r"\s+", " ", rep_text).strip()
                if len(rep_text) > 500:
                    rep_text = rep_text[:500] + "..."
                comments.append(f"[{idx}] {rep_text}".strip())

            if keywords:
                content = f"{title} {' '.join(comments)}"
                if not matches_keywords(content, keywords):
                    return None

            return [
                post_time.strftime("%m/%d/%Y %H:%M"),
                "uscommunity",
                title,
                comments[0][5:] if comments else "",
                link,
                " ".join(comments),
            ]
        except Exception:
            return None
