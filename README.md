# IVOC Data Scraper

A desktop GUI application that scrapes:
- **Samsung US Community** discussion boards
- **Reddit** (hybrid PRAW + Pushshift)

The app exports results to **CSV + styled Excel (XLSX)** and can optionally email the report.

## 🧰 Requirements

- **Python 3.10+**
- Windows / macOS / Linux
- Internet connection
- Reddit API credentials (free)
- Optional: Gmail App Password (for email)

## Setup

### Create `.env` file

Copy the example:

```powershell
copy .env.example .env
```

Edit `.env` and fill in **your own credentials**:

```env
# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=RedditScraper/3.0 by u/YourRedditName
REDDIT_TIMEOUT_SEC=15

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your_gmail_app_password
```
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

###  Run the application

```powershell
python main.py
```

The GUI will open.

## 🖥️ GUI Usage

### Modes

* **Date Range**: Scrape between two dates
* **Keywords** (optional): Filter results (comma-separated)

### Output

* Files are saved in:

  ```
  data/
    MM_DD_YY_morning.csv
    MM_DD_YY_morning.xlsx
  ```

