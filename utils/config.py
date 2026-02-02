from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from utils.paths import data_dir


@dataclass(frozen=True)
class RedditConfig:
    client_id: str
    client_secret: str
    user_agent: str
    timeout_sec: int = 15


@dataclass(frozen=True)
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    user: str = ""
    password: str = ""


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    reddit: RedditConfig
    email: EmailConfig

    max_pages_uscommunity: int = 10
    reddit_recent_days_cutoff: int = 3

    reddit_max_workers: int = 10
    uscommunity_max_workers: int = 15


BANNED_FLAIRS: set[str] = {
    "camera", "tip", "photography", "review", "news", "psa", "spoiler",
    "update", "advice needed", "general", "impression", "wallpaper",
    "samsung official", "scheduled megathread", "rumor", "pro tip",
    "samsung tv", "tips & tricks", "cases", "screen protectors",
    "purchase", "availability", "general discussion", "meme", "leak",
    "deal", "watch band", "iphone",
}

REDDIT_SUBS: list[str] = [
    "GalaxyBook", "samsunggalaxy", "GalaxyFold", "galaxyzflip", "samsung", "galaxybuds",
    "GalaxyWatch", "galaxywatch4", "GalaxyS21", "GalaxyS21FE", "S22Ultra", "S22", "GalaxyS22",
    "GalaxyTab", "zfold4", "oneui", "GalaxyS23", "GalaxyS23Ultra", "S23Ultra", "S23", "Android",
    "Tmobile", "ATT", "Verizon", "GalaxyA54", "Official_S23FE", "GalaxyS24Ultra", "GalaxyS24",
    "Galaxyring", "S24FE", "S24Ultra", "GalaxyS25", "GalaxyS25Plus", "GalaxyS25Ultra", "S25Ultra",
    "S25Edge", "GalaxyA36", "GalaxyA56", "GalaxyA16", "GalaxyWatch8", "Galaxyflip7", "Galaxy_XR",
    "GalaxyXR", "AndroidXR", "virtualreality", "ZFlip7", "S25FE", "SamsungHelp", "Samsung_GoodLock",
]

US_LINKS: list[str] = [
    "https://us.community.samsung.com/t5/Computers/bd-p/get-help-computers-and-printers",
    "https://us.community.samsung.com/t5/Galaxy-S21/bd-p/GalaxyS21",
    "https://us.community.samsung.com/t5/Note20/bd-p/get-help-galaxy-note20",
    "https://us.community.samsung.com/t5/Galaxy-S20/bd-p/get-help-galaxy-s20",
    "https://us.community.samsung.com/t5/Galaxy-Z-Flip/bd-p/get-help-galaxy-ZFlip",
    "https://us.community.samsung.com/t5/Galaxy-Fold/bd-p/Gethelp-galaxy-fold",
    "https://us.community.samsung.com/t5/Galaxy-Note-Phones/bd-p/get-help-phones-galaxy-note-phones",
    "https://us.community.samsung.com/t5/Galaxy-S-Phones/bd-p/get-help-phones-galaxy-s-phones",
    "https://us.community.samsung.com/t5/Other-Mobile-Devices/bd-p/get-help-phones-other-mobile-devices",
    "https://us.community.samsung.com/t5/Galaxy-S22/bd-p/GalaxyS22",
    "https://us.community.samsung.com/t5/Galaxy-Watch/bd-p/get-help-wearables-galaxy-watch",
    "https://us.community.samsung.com/t5/Galaxy-Buds/bd-p/get-help-galaxy-buds",
    "https://us.community.samsung.com/t5/Gear-and-Gear-Fit/bd-p/get-help-wearables-gear-and-gear-fit",
    "https://us.community.samsung.com/t5/Android-12/bd-p/Android12",
    "https://us.community.samsung.com/t5/Tablets/bd-p/get-help-tablets",
    "https://us.community.samsung.com/t5/Galaxy-S23/bd-p/GalaxyS23",
    "https://us.community.samsung.com/t5/Galaxy-S24/bd-p/GalaxyS24",
    "https://us.community.samsung.com/t5/Galaxy-Ring/bd-p/GalaxyRing",
    "https://us.community.samsung.com/t5/Galaxy-S25/bd-p/GalaxyS25",
    "https://us.community.samsung.com/t5/Galaxy-XR/bd-p/GalaxyXR",
]


def load_config() -> AppConfig:
    reddit = RedditConfig(
        client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
        client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
        user_agent=os.environ.get("REDDIT_USER_AGENT", "RedditScraper/3.0"),
        timeout_sec=int(os.environ.get("REDDIT_TIMEOUT_SEC", "15")),
    )
    email = EmailConfig(
        smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        user=os.environ.get("SMTP_USER", ""),
        password=os.environ.get("SMTP_PASS", ""),
    )
    return AppConfig(data_dir=data_dir(), reddit=reddit, email=email)
