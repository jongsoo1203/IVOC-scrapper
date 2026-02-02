from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import praw
from psaw import PushshiftAPI

from utils.config import AppConfig, BANNED_FLAIRS
from utils.keywords import matches_keywords

log = logging.getLogger("tools.reddit")


def _safe_ascii(text: str) -> str:
    # Keep it simple + consistent with your earlier approach:
    return "".join(ch for ch in text if ord(ch) <= 255)


@dataclass
class RedditScraper:
    cfg: AppConfig

    def __post_init__(self) -> None:
        self.reddit = praw.Reddit(
            client_id=self.cfg.reddit.client_id,
            client_secret=self.cfg.reddit.client_secret,
            user_agent=self.cfg.reddit.user_agent,
            timeout=self.cfg.reddit.timeout_sec,
        )
        self.pushshift = PushshiftAPI()

    def scrape(self, subreddit: str, start: datetime, end: datetime, keywords: list[str]) -> list[list[str]]:
        days_ago = (datetime.now() - start).days
        if days_ago <= self.cfg.reddit_recent_days_cutoff:
            log.info("r/%s using PRAW (recent)", subreddit)
            return self._scrape_praw(subreddit, start, end, keywords)

        log.info("r/%s using PSAW (historical)", subreddit)
        return self._scrape_psaw(subreddit, start, end, keywords)

    def _scrape_psaw(self, subreddit: str, start: datetime, end: datetime, keywords: list[str]) -> list[list[str]]:
        start_epoch = int(start.timestamp())
        end_epoch = int(end.timestamp())

        gen = self.pushshift.search_submissions(
            subreddit=subreddit,
            after=start_epoch,
            before=end_epoch,
            filter=["id", "created_utc", "title", "author", "link_flair_text"],
            limit=5000,
        )

        post_ids: list[str] = []
        for post in gen:
            flair = (str(getattr(post, "link_flair_text", "")) or "").lower().strip()
            if flair not in BANNED_FLAIRS:
                post_ids.append(post.id)

        rows: list[list[str]] = []
        for pid in post_ids:
            row = self._fetch_post_by_id(pid, start, end, keywords)
            if row:
                rows.append(row)
        return rows

    def _scrape_praw(self, subreddit: str, start: datetime, end: datetime, keywords: list[str]) -> list[list[str]]:
        sub = self.reddit.subreddit(subreddit)
        seen: set[str] = set()
        submissions = []

        for s in sub.new(limit=700):
            post_time = datetime.fromtimestamp(s.created_utc)
            if post_time < start:
                break
            if start <= post_time <= end and s.id not in seen:
                submissions.append(s)
                seen.add(s.id)

        for s in sub.hot(limit=200):
            post_time = datetime.fromtimestamp(s.created_utc)
            if start <= post_time <= end and s.id not in seen:
                submissions.append(s)
                seen.add(s.id)

        rows: list[list[str]] = []
        for s in submissions:
            row = self._process_submission(s, start, end, keywords)
            if row:
                rows.append(row)
        return rows

    def _fetch_post_by_id(self, post_id: str, start: datetime, end: datetime, keywords: list[str]) -> Optional[list[str]]:
        try:
            s = self.reddit.submission(id=post_id)
            return self._process_submission(s, start, end, keywords)
        except Exception:
            return None

    def _process_submission(self, s, start: datetime, end: datetime, keywords: list[str]) -> Optional[list[str]]:
        flair = (str(getattr(s, "link_flair_text", "")) or "").lower().strip()
        if flair in BANNED_FLAIRS:
            return None

        post_time = datetime.fromtimestamp(s.created_utc)
        if not (start <= post_time <= end):
            return None

        postlink = "https://www.reddit.com" + s.permalink

        title = (s.title or "").replace(",", " ").replace('"', "'")
        title = _safe_ascii(title)

        desc = (s.selftext or "").replace(",", " ").replace("\n", " ").replace('"', "'")
        desc = _safe_ascii(desc) or (s.url or "")

        comments_list: list[str] = []
        try:
            s.comments.replace_more(limit=1)
            for count, c in enumerate(s.comments.list()[:10], 1):
                body = getattr(c, "body", "") or ""
                if body in ("", "[deleted]", "[removed]"):
                    continue

                body = body.replace(",", " ").replace("\n", " ").replace("\r", " ").replace('"', "'")
                body = re.sub(r"[\u200e\u200f]", "", body)
                body = _safe_ascii(body)

                if len(body) > 500:
                    body = body[:500] + "..."

                comments_list.append(f"[{count}] {body}".strip())
        except Exception:
            pass

        if keywords:
            content = f"{title} {desc} {' '.join(comments_list)}"
            if not matches_keywords(content, keywords):
                return None

        return [
            post_time.strftime("%m/%d/%Y %H:%M"),
            "reddit",
            title,
            desc,
            postlink,
            " ".join(comments_list),
        ]
