import csv
import datetime as dt
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)


def create_fast_session():
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def quick_extract_date(session, link):
    try:
        r = session.get(link, timeout=5)
        soup = BeautifulSoup(r.content, "lxml")

        lfd_single = soup.find(class_="local-friendly-date")
        asd = soup.find(class_="DateTime lia-message-posted-on lia-component-common-widget-date")
        src = lfd_single["title"] if (lfd_single and lfd_single.has_attr("title")) else str(asd)

        m = re.search(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)", src or "")
        if m:
            return dt.datetime.strptime(
                f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}",
                "%m-%d-%Y %I:%M %p"
            )
    except Exception:
        pass
    return None


def fetch_link_fast(session, link, start_date, end_date, keywords):
    try:
        r = session.get(link, timeout=8)
        soup = BeautifulSoup(r.content, "lxml")

        asd = soup.find(class_="DateTime lia-message-posted-on lia-component-common-widget-date")
        lfd_single = soup.find(class_="local-friendly-date")
        src = lfd_single["title"] if (lfd_single and lfd_single.has_attr("title")) else str(asd)

        m = re.search(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)", src or "")
        if not m:
            return None

        post_time = dt.datetime.strptime(
            f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}",
            "%m-%d-%Y %I:%M %p"
        )

        if post_time < start_date or post_time > end_date:
            return None

        title_tag = soup.find("h2") or soup.find("h1") or soup.find("meta", {"property": "og:title"})
        title = (title_tag.get_text() if hasattr(title_tag, "get_text")
                 else title_tag.get("content", "") if title_tag else "").strip()

        comments = []
        replies = soup.find_all("div", {"class": "lia-message-body-content"})[:8]
        for count, rep in enumerate(replies, 1):
            rep_text = rep.get_text().replace("\n", " ").replace("\t", "")
            rep_text = re.sub(r"[\u200e\u200f]", "", rep_text)
            rep_text = re.sub(r"\s+", " ", rep_text)

            if len(rep_text) > 500:
                rep_text = rep_text[:500] + "..."

            comments.append(f"[{count}] {rep_text}".strip())

        if keywords:
            content_to_check = f"{title} {' '.join(comments)}"
            if not matches_keywords(content_to_check, keywords):
                return None

        return [
            post_time.strftime("%m/%d/%Y %H:%M"),
            "uscommunity",
            title,
            comments[0][5:] if comments else "",
            link,
            str(comments),
        ]

    except Exception:
        return None


def us_community_deep_scrape(search_url, start_date, end_date, keywords, fn, max_pages=10, progress_callback=None):
    session = create_fast_session()
    all_links = []
    page = 1
    found_old_enough = False

    print("[US Community] Starting deep scrape...")

    while page <= max_pages and not found_old_enough:
        try:
            url = f"{search_url}?page={page}" if page > 1 else search_url
            r = session.get(url, timeout=10)
            soup = BeautifulSoup(r.content, "lxml")

            urls = soup.find_all("h3")
            link_regex = re.findall(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                str(urls),
            )

            if not link_regex:
                print(f"[US Community] No more posts found at page {page}")
                break

            if page > 1:
                sample_date = quick_extract_date(session, link_regex[0])
                if sample_date and sample_date < start_date:
                    print(f"[US Community] Reached posts older than start_date at page {page}")
                    found_old_enough = True
                    break

            all_links.extend(link_regex)
            print(f"[US Community] Scraped page {page}, {len(link_regex)} links found")

            next_button = soup.find("a", {"rel": "next"})
            if not next_button:
                break

            page += 1

        except Exception as e:
            print(f"[US Community] Error on page {page}: {e}")
            break

    all_links = list(set(all_links))
    total_links = len(all_links)
    print(f"[US Community] Total links collected: {total_links}")

    with open(fn, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_ALL)

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(fetch_link_fast, session, link, start_date, end_date, keywords)
                for link in all_links
            ]

            for i, future in enumerate(as_completed(futures), 1):
                try:
                    row = future.result(timeout=10)
                    if row:
                        writer.writerow(row)
                        f.flush()
                except Exception:
                    pass

                if progress_callback and i % 10 == 0:
                    progress_callback(i, total_links, f"US Community: {i}/{total_links}")
