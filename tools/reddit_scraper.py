import csv
import datetime as dt
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import praw
from psaw import PushshiftAPI


def matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)


BANNED_LIST = {
    "camera", "tip", "photography", "review", "news", "psa", "spoiler",
    "update", "advice needed", "general", "impression", "wallpaper",
    "samsung official", "scheduled megathread", "rumor", "pro tip",
    "samsung tv", "tips & tricks", "cases", "screen protectors",
    "purchase", "availability", "general discussion", "meme", "leak",
    "deal", "watch band", "iphone"
}


def reddit_scraper_historical(reddit_config, subreddit, start_date, end_date, keywords, fn, progress_callback=None):
    """
    Same behavior as your original:
    - last 3 days -> PRAW
    - older -> PSAW -> then PRAW by id
    """
    days_ago = (datetime.now() - start_date).days

    if days_ago <= 3:
        print(f"[{subreddit}] Using PRAW (recent data)")
        return reddit_scraper_praw(reddit_config, subreddit, start_date, end_date, keywords, fn, progress_callback)
    else:
        print(f"[{subreddit}] Using PSAW (historical data from {days_ago} days ago)")
        return reddit_scraper_psaw(reddit_config, subreddit, start_date, end_date, keywords, fn, progress_callback)


def reddit_scraper_psaw(reddit_config, subreddit, start_date, end_date, keywords, fn, progress_callback=None):
    api = PushshiftAPI()
    reddit = praw.Reddit(
        client_id=reddit_config.client_id,
        client_secret=reddit_config.client_secret,
        user_agent=reddit_config.user_agent,
        timeout=20,
    )

    start_epoch = int(start_date.timestamp())
    end_epoch = int(end_date.timestamp())

    print(f"[{subreddit}] Searching PushShift for posts from {start_date.date()} to {end_date.date()}...")

    try:
        gen = api.search_submissions(
            subreddit=subreddit,
            after=start_epoch,
            before=end_epoch,
            filter=["id", "created_utc", "title", "author", "link_flair_text"],
            limit=5000
        )

        post_ids = []
        for post in gen:
            flair = (str(getattr(post, "link_flair_text", "")) or "").lower().strip()
            if flair not in BANNED_LIST:
                post_ids.append(post.id)

        print(f"[{subreddit}] Found {len(post_ids)} posts from PushShift")
        if not post_ids:
            print(f"[{subreddit}] No posts found in date range")
            return

        total = len(post_ids)

        with open(fn, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_ALL)

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(fetch_reddit_post_by_id, reddit, post_id, start_date, end_date, keywords): post_id
                    for post_id in post_ids
                }

                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        row = future.result(timeout=15)
                        if row:
                            writer.writerow(row)
                            f.flush()
                    except Exception:
                        pass

                    if progress_callback and i % 20 == 0:
                        progress_callback(i, total, f"Reddit r/{subreddit}: {i}/{total}")

                    if i % 100 == 0:
                        time.sleep(3)

        print(f"[{subreddit}] Completed scraping")

    except Exception as e:
        print(f"[{subreddit}] Error in PSAW scraper: {e}")


def reddit_scraper_praw(reddit_config, subreddit, start_date, end_date, keywords, fn, progress_callback=None):
    reddit = praw.Reddit(
        client_id=reddit_config.client_id,
        client_secret=reddit_config.client_secret,
        user_agent=reddit_config.user_agent,
        timeout=15,
    )

    posts_collected = []
    seen_ids = set()

    try:
        sub = reddit.subreddit(subreddit)

        for subm in sub.new(limit=700):
            post_time = dt.datetime.fromtimestamp(subm.created_utc)
            if post_time < start_date:
                break
            if post_time <= end_date and subm.id not in seen_ids:
                posts_collected.append(subm)
                seen_ids.add(subm.id)

        for subm in sub.hot(limit=200):
            post_time = dt.datetime.fromtimestamp(subm.created_utc)
            if start_date <= post_time <= end_date and subm.id not in seen_ids:
                posts_collected.append(subm)
                seen_ids.add(subm.id)

        total = len(posts_collected)

        with open(fn, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_ALL)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(process_post_fast, subm, start_date, end_date, keywords): subm
                    for subm in posts_collected
                }

                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        row = future.result(timeout=10)
                        if row:
                            writer.writerow(row)
                            f.flush()
                    except Exception:
                        pass

                    if progress_callback and i % 20 == 0:
                        progress_callback(i, total, f"Reddit r/{subreddit}: {i}/{total}")

    except Exception as e:
        print(f"Error in PRAW scraper for r/{subreddit}: {e}")


def fetch_reddit_post_by_id(reddit, post_id, start_date, end_date, keywords):
    try:
        submission = reddit.submission(id=post_id)

        flair = (str(submission.link_flair_text) or "").lower().strip()
        if flair in BANNED_LIST:
            return None

        post_time = dt.datetime.fromtimestamp(submission.created_utc)
        if post_time < start_date or post_time > end_date:
            return None

        postlink = "https://www.reddit.com" + submission.permalink
        title = (submission.title or "").replace(",", " ").replace('"', "'")
        desc = (submission.selftext or "").replace(",", " ").replace("\n", " ").replace('"', "'")
        desc = "".join(ch for ch in desc if ord(ch) <= 255) or (submission.url or "")

        comments_list = []
        try:
            submission.comments.replace_more(limit=1)
            all_comments = submission.comments.list()

            for count, c in enumerate(all_comments[:10], 1):
                body = getattr(c, "body", "") or ""
                if body in ("", "[deleted]", "[removed]"):
                    continue

                body = body.replace(",", " ").replace("\n", " ").replace("\r", " ").replace('"', "'")
                body = "".join(ch for ch in body if ord(ch) <= 255)
                body = re.sub(r"[\u200e\u200f]", "", body)

                if len(body) > 500:
                    body = body[:500] + "..."

                comments_list.append(f"[{count}] {body}".strip())
        except Exception:
            pass

        if keywords:
            content_to_check = f"{title} {desc} {' '.join(comments_list)}"
            if not matches_keywords(content_to_check, keywords):
                return None

        return [
            post_time.strftime("%m/%d/%Y %H:%M"),
            "reddit",
            title,
            desc,
            postlink,
            " ".join(comments_list),
        ]

    except Exception:
        return None


def process_post_fast(subm, start_date, end_date, keywords):
    try:
        flair = (str(subm.link_flair_text) or "").lower().strip()
        if flair in BANNED_LIST:
            return None

        post_time = dt.datetime.fromtimestamp(subm.created_utc)
        if post_time < start_date or post_time > end_date:
            return None

        postlink = "https://www.reddit.com" + subm.permalink
        title = (subm.title or "").replace(",", " ").replace('"', "'")
        desc = (subm.selftext or "").replace(",", " ").replace("\n", " ").replace('"', "'")
        desc = "".join(ch for ch in desc if ord(ch) <= 255) or (subm.url or "")

        comments_list = []
        try:
            subm.comments.replace_more(limit=1)
            all_comments = subm.comments.list()

            for count, c in enumerate(all_comments[:10], 1):
                body = getattr(c, "body", "") or ""
                if body in ("", "[deleted]", "[removed]"):
                    continue

                body = body.replace(",", " ").replace("\n", " ").replace("\r", " ").replace('"', "'")
                body = "".join(ch for ch in body if ord(ch) <= 255)
                body = re.sub(r"[\u200e\u200f]", "", body)

                if len(body) > 500:
                    body = body[:500] + "..."

                comments_list.append(f"[{count}] {body}".strip())
        except Exception:
            pass

        if keywords:
            content_to_check = f"{title} {desc} {' '.join(comments_list)}"
            if not matches_keywords(content_to_check, keywords):
                return None

        return [
            post_time.strftime("%m/%d/%Y %H:%M"),
            "reddit",
            title,
            desc,
            postlink,
            " ".join(comments_list),
        ]
    except Exception:
        return None
