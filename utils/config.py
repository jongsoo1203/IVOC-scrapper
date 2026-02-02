import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class RedditConfig:
    client_id: str
    client_secret: str
    user_agent: str


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    to: str


def load_env() -> None:
    # loads .env if present
    load_dotenv()


def get_reddit_config() -> RedditConfig:
    load_env()
    client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
    user_agent = os.getenv("REDDIT_USER_AGENT", "RedditScraper/3.0 by u/YourUser").strip()

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Reddit credentials. Create a .env file (copy from .env.example) and set:\n"
            "REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT"
        )

    return RedditConfig(client_id=client_id, client_secret=client_secret, user_agent=user_agent)


def get_smtp_config() -> SmtpConfig:
    load_env()
    host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    port_str = os.getenv("SMTP_PORT", "587").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "").strip()
    to = os.getenv("SMTP_TO", user).strip()

    if not user or not password:
        raise RuntimeError(
            "Missing SMTP credentials. Create a .env file (copy from .env.example) and set:\n"
            "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS (and optionally SMTP_TO)"
        )

    try:
        port = int(port_str)
    except ValueError:
        port = 587

    return SmtpConfig(host=host, port=port, user=user, password=password, to=to)


# keep the same lists as your original file
REDDIT_LINKS = [
    "GalaxyBook", "samsunggalaxy", "GalaxyFold", "galaxyzflip", "samsung", "galaxybuds",
    "GalaxyWatch", "galaxywatch4", "GalaxyS21", "GalaxyS21FE", "S22Ultra", "S22", "GalaxyS22",
    "GalaxyTab", "zfold4", "oneui", "GalaxyS23", "GalaxyS23Ultra", "S23Ultra", "S23",
    "Android", "Tmobile", "ATT", "Verizon", "GalaxyA54", "Official_S23FE", "GalaxyS24Ultra",
    "GalaxyS24", "Galaxyring", "S24FE", "S24Ultra", "GalaxyS25", "GalaxyS25Plus",
    "GalaxyS25Ultra", "S25Ultra", "S25Edge", "GalaxyA36", "GalaxyA56", "GalaxyA16",
    "GalaxyWatch8", "Galaxyflip7", "Galaxy_XR", "GalaxyXR", "AndroidXR", "virtualreality",
    "ZFlip7", "S25FE", "SamsungHelp", "Samsung_GoodLock"
]

US_LINKS = [
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
