# ============================================================
# Ireland Job Market Scraper — Data Collection Pipeline
# ============================================================
# Author:      Ishan Kasare
# GitHub:      https://github.com/Ishankasare/Ireland-Job-Market-Analytics
# LinkedIn:    https://www.linkedin.com/in/ishan-kasare/
#
# Description:
#   Scrapes Data Analyst, Data Science and Internship job
#   listings from LinkedIn and IrishJobs.ie, cleans and stores
#   results in SQLite database for analysis and dashboarding.
#
# Usage:
#   pip install -r requirements.txt
#   python src/scraper.py
# ============================================================

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import time
import re
import logging
import os
from datetime import datetime

# ── Logging setup ────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────
DB_PATH = "data/jobs.db"
SEARCH_TERMS = [
    "data analyst",
    "data scientist",
    "data engineer",
    "business intelligence analyst",
    "data analyst internship",
    "data science internship"
]
DELAY = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ============================================================
# LINKEDIN SCRAPER
# ============================================================

def scrape_linkedin(search_term: str, location: str = "Ireland", pages: int = 5) -> list:
    jobs = []

    for page in range(0, pages * 25, 25):
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={requests.utils.quote(search_term)}"
            f"&location={requests.utils.quote(location)}"
            f"&start={page}"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.find_all("div", class_=re.compile("base-card"))
            if not cards:
                cards = soup.find_all("li", class_=re.compile("result-card|jobs-search"))

            if not cards:
                log.warning(f"LinkedIn | No cards on page {page // 25 + 1} for '{search_term}'")
                break

            for card in cards:
                job = parse_linkedin_card(card, search_term)
                if job:
                    jobs.append(job)

            log.info(f"LinkedIn | '{search_term}' | Page {page // 25 + 1} | {len(cards)} found")
            time.sleep(DELAY)

        except Exception as e:
            log.error(f"LinkedIn error — '{search_term}' page {page}: {e}")
            time.sleep(DELAY)
            continue

    return jobs


def parse_linkedin_card(card, search_term: str):
    try:
        title_el = (
            card.find("h3", class_=re.compile("base-search-card__title")) or
            card.find("h3") or
            card.find("span", class_=re.compile("title"))
        )
        company_el = (
            card.find("h4", class_=re.compile("base-search-card__subtitle")) or
            card.find("h4") or
            card.find("a", class_=re.compile("hidden-nested-link"))
        )
        location_el = card.find("span", class_=re.compile("job-search-card__location|location"))
        posted_el = card.find("time") or card.find("span", class_=re.compile("listed-time|date"))
        link_el = card.find("a", href=True)

        title = title_el.get_text(strip=True) if title_el else None
        company = company_el.get_text(strip=True) if company_el else None

        if not title or not company:
            return None

        return {
            "title": title,
            "company": company,
            "location": location_el.get_text(strip=True) if location_el else "Ireland",
            "salary": "Not specified",
            "summary": "",
            "posted": posted_el.get("datetime", posted_el.get_text(strip=True)) if posted_el else None,
            "url": link_el["href"] if link_el else None,
            "source": "LinkedIn",
            "search_term": search_term,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        log.error(f"LinkedIn card parse error: {e}")
        return None


# ============================================================
# IRISHJOBS.IE SCRAPER
# ============================================================

def scrape_irishjobs(search_term: str, pages: int = 5) -> list:
    jobs = []

    for page in range(1, pages + 1):
        url = (
            f"https://www.irishjobs.ie/ShowResults.aspx"
            f"?Keywords={requests.utils.quote(search_term)}"
            f"&Location=101"
            f"&Page={page}"
            f"&SortType=date"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.find_all("div", class_=re.compile("job|vacancy|listing"), limit=50)
            cards = [c for c in cards if c.find("h2") or c.find("h3") or c.find("a", class_=re.compile("title|job"))]

            if not cards:
                log.warning(f"IrishJobs | No cards on page {page} for '{search_term}'")
                break

            for card in cards:
                job = parse_irishjobs_card(card, search_term)
                if job:
                    jobs.append(job)

            log.info(f"IrishJobs | '{search_term}' | Page {page} | {len(cards)} found")
            time.sleep(DELAY)

        except Exception as e:
            log.error(f"IrishJobs error — '{search_term}' page {page}: {e}")
            time.sleep(DELAY)
            continue

    return jobs


def parse_irishjobs_card(card, search_term: str):
    try:
        title_el = card.find("h2") or card.find("h3") or card.find("a", class_=re.compile("title|job-title"))
        company_el = card.find("span", class_=re.compile("company|employer")) or card.find("p", class_=re.compile("company"))
        location_el = card.find("span", class_=re.compile("location|city"))
        salary_el = card.find("span", class_=re.compile("salary"))
        posted_el = card.find("span", class_=re.compile("date|posted|time"))
        link_el = card.find("a", href=True)

        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        return {
            "title": title,
            "company": company_el.get_text(strip=True) if company_el else "Not specified",
            "location": location_el.get_text(strip=True) if location_el else "Ireland",
            "salary": salary_el.get_text(strip=True) if salary_el else "Not specified",
            "summary": "",
            "posted": posted_el.get_text(strip=True) if posted_el else None,
            "url": ("https://www.irishjobs.ie" + link_el["href"]) if link_el and link_el["href"].startswith("/") else (link_el["href"] if link_el else None),
            "source": "IrishJobs.ie",
            "search_term": search_term,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        log.error(f"IrishJobs card parse error: {e}")
        return None


# ============================================================
# DATA CLEANING
# ============================================================

def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning scraped data...")

    if df.empty:
        log.warning("No data to clean")
        return df

    df = df.dropna(subset=["title"])
    df = df[df["title"].str.strip() != ""]
    df["company"] = df["company"].fillna("Not specified")
    df = df.drop_duplicates(subset=["title", "company"])
    df["title"] = df["title"].str.strip().str.title()
    df["company"] = df["company"].str.strip().str.title()
    df["location"] = df["location"].fillna("Ireland").str.strip()
    df["job_type"] = df["title"].apply(classify_job_type)
    df["seniority"] = df["title"].apply(classify_seniority)
    df["skills_mentioned"] = df["summary"].apply(extract_skills)
    df["salary_clean"] = df["salary"].apply(clean_salary)

    log.info(f"Cleaned: {len(df)} rows remaining")
    return df


def classify_job_type(title: str) -> str:
    title = str(title).lower()
    if any(x in title for x in ["intern", "internship", "graduate", "grad", "placement"]):
        return "Internship / Graduate"
    elif any(x in title for x in ["scientist", "science"]):
        return "Data Scientist"
    elif any(x in title for x in ["engineer", "engineering"]):
        return "Data Engineer"
    elif any(x in title for x in ["bi ", "business intelligence", "power bi", "tableau"]):
        return "BI / Visualisation"
    elif any(x in title for x in ["analyst"]):
        return "Data Analyst"
    else:
        return "Other"


def classify_seniority(title: str) -> str:
    title = str(title).lower()
    if any(x in title for x in ["intern", "internship", "junior", "graduate", "entry", "jr", "placement"]):
        return "Junior / Entry"
    elif any(x in title for x in ["senior", "sr.", "lead", "principal", "head", "staff"]):
        return "Senior"
    elif any(x in title for x in ["manager", "director", "vp", "chief"]):
        return "Manager / Director"
    else:
        return "Mid-Level"


def extract_skills(summary: str) -> str:
    if not summary:
        return ""
    summary = str(summary).lower()
    skills = [
        "python", "sql", "power bi", "tableau", "excel",
        "machine learning", "azure", "aws", "gcp", "dbt",
        "airflow", "pandas", "scikit-learn", "tensorflow",
        "pytorch", "snowflake", "databricks", "spark"
    ]
    found = [s for s in skills if re.search(r'\b' + re.escape(s) + r'\b', summary)]
    return ", ".join(found)


def clean_salary(salary: str) -> str:
    if not salary or str(salary).strip() in ["Not specified", "nan", ""]:
        return "Not specified"
    if any(x in str(salary).lower() for x in ["€", "£", "k", "per", "year", "annual", "000"]):
        return str(salary).strip()
    return "Not specified"


# ============================================================
# STORAGE
# ============================================================

def save_to_sqlite(df: pd.DataFrame, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    df.to_sql("jobs", conn, if_exists="append", index=False)
    conn.close()
    log.info(f"Saved {len(df)} records to {db_path}")


def save_to_csv(df: pd.DataFrame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = f"data/processed/jobs_{timestamp}.csv"
    df.to_csv(path, index=False)
    log.info(f"CSV saved to {path}")


# ============================================================
# MAIN
# ============================================================

def run_pipeline():
    log.info("=" * 60)
    log.info("Ireland Job Market Scraper — Pipeline Starting")
    log.info("=" * 60)

    all_jobs = []

    for term in SEARCH_TERMS:
        log.info(f"--- Scraping: '{term}' ---")

        linkedin_jobs = scrape_linkedin(term, location="Ireland", pages=3)
        all_jobs.extend(linkedin_jobs)
        log.info(f"LinkedIn: {len(linkedin_jobs)} listings")

        irishjobs = scrape_irishjobs(term, pages=3)
        all_jobs.extend(irishjobs)
        log.info(f"IrishJobs: {len(irishjobs)} listings")

    log.info(f"Total raw collected: {len(all_jobs)}")

    if not all_jobs:
        log.error("No data collected. Check internet connection or try again later.")
        return pd.DataFrame()

    df = pd.DataFrame(all_jobs)
    df = clean_jobs(df)

    if df.empty:
        log.error("Empty after cleaning.")
        return df

    save_to_sqlite(df)
    save_to_csv(df)

    log.info(f"Pipeline complete — {len(df)} clean listings saved")
    return df


if __name__ == "__main__":
    run_pipeline()
