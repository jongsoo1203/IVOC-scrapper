# Scraper App

Scrapes:
- Samsung US Community boards
- Reddit subreddits (PRAW + PSAW hybrid)

Outputs:
- CSV + XLSX saved to `data/`


## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -U pip
pip install -e .
```
Create .env from .env.example and set credentials.

Run GUI
```
scraper-gui
```

## One important note (Tkinter packaging)
On Windows, Tkinter works out-of-the-box. On some Linux environments you may need OS packages. That’s normal.
