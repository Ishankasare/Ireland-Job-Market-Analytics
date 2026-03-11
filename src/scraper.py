# ============================================================
# Ireland Job Market Scraper — Data Collection Pipeline
# ============================================================
# Author:      Ishan Kasare
# GitHub:      https://github.com/Ishankasare/Ireland-Job-Market-Analytics
# LinkedIn:    https://www.linkedin.com/in/ishan-kasare/
#
# Description:
#   Scrapes Data Analyst, Data Science and Internship job
#   listings from Indeed.ie and Jobs.ie, cleans and stores
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
from datetime import datetime
from fake_useragent import UserAgent

# ── Logging setup ────────────────────────────────────────────
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
    "business intelligence",
    "data analyst internship",
    "data science internship"
]
LOCATIONS = ["Dublin", "Ireland"]
DELAY_BETWEEN_REQUESTS = 2  # seconds — be polite to servers


# ============================================================
# INDEED.IE SCRAPER
# ============================================================

def scrape_indeed(search_term: str, location: str, pages: int = 5) -> list[dict]:
    """Scrape job listings from Indeed.ie for a given search term and location."""
    ua = UserAgent()
    jobs = []

    for page in range(0, pages * 10, 10):
        url = (
            f"https://ie.indeed.com/jobs"
            f"?q={search_term.replace(' ', '+')}"
            f"&l={location.replace(' ', '+')}"
            f"&start={page}"
        )
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.find_all("div", class_="job_seen_beacon")
            if not cards:
                log.warning(f"No cards found on page {page // 10 + 1} for '{search_term}'")
                break

            for card in cards:
                job = parse_indeed_card(card, search_term)
                if job:
                    jobs.append(job)

            log.info(f"Indeed | '{search_term}' | Page {page // 10 + 1} | {len(cards)} listings")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            log.error(f"Indeed scrape error on page {page}: {e}")
            break

    return jobs


def parse_indeed_card(card, search_term: str) -> dict | None:
    """Extract structured data from a single Indeed job card."""
    try:
        title = card.find("span", {"id": re.compile("jobTitle")})
        company = card.find("span", {"data-testid": "company-name"})
        location = card.find("div", {"data-testid": "text-location"})
        salary = card.find("div", {"class": re.compile("salary")})
        summary = card.find("div", {"class": re.compile("job-snippet")})
        posted = card.find("span", {"class": re.compile("date")})

        return {
            "title": title.get_text(strip=True) if title else None,
            "company": company.get_text(strip=True) if company else None,
            "location": location.get_text(strip=True) if location else None,
            "salary": salary.get_text(strip=True) if salary else "Not specified",
            "summary": summary.get_text(strip=True) if summary else None,
            "posted": posted.get_text(strip=True) if posted else None,
            "source": "Indeed.ie",
            "search_term": search_term,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        log.error(f"Error parsing Indeed card: {e}")
        return None


# ============================================================
# JOBS.IE SCRAPER
# ============================================================

def scrape_jobsie(search_term: str, pages: int = 5) -> list[dict]:
    """Scrape job listings from Jobs.ie for a given search term."""
    ua = UserAgent()
    jobs = []

    for page in range(1, pages + 1):
        url = (
            f"https://www.jobs.ie/jobs/"
            f"?q={search_term.replace(' ', '+')}"
            f"&page={page}"
        )
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.find_all("article", class_=re.compile("job"))
            if not cards:
                log.warning(f"No cards found on page {page} for '{search_term}' on Jobs.ie")
                break

            for card in cards:
                job = parse_jobsie_card(card, search_term)
                if job:
                    jobs.append(job)

            log.info(f"Jobs.ie | '{search_term}' | Page {page} | {len(cards)} listings")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            log.error(f"Jobs.ie scrape error on page {page}: {e}")
            break

    return jobs


def parse_jobsie_card(card, search_term: str) -> dict | None:
    """Extract structured data from a single Jobs.ie job card."""
    try:
        title = card.find("h2") or card.find("h3")
        company = card.find("span", class_=re.compile("company"))
        location = card.find("span", class_=re.compile("location"))
        salary = card.find("span", class_=re.compile("salary"))
        summary = card.find("p", class_=re.compile("description|summary"))
        posted = card.find("time") or card.find("span", class_=re.compile("date|posted"))

        return {
            "title": title.get_text(strip=True) if title else None,
            "company": company.get_text(strip=True) if company else None,
            "location": location.get_text(strip=True) if location else None,
            "salary": salary.get_text(strip=True) if salary else "Not specified",
            "summary": summary.get_text(strip=True) if summary else None,
            "posted": posted.get_text(strip=True) if posted else None,
            "source": "Jobs.ie",
            "search_term": search_term,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        log.error(f"Error parsing Jobs.ie card: {e}")
        return None


# ============================================================
# DATA CLEANING
# ============================================================

def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardise the raw scraped job data."""
    log.info("Cleaning scraped data...")

    # Drop rows with no title or company
    df = df.dropna(subset=["title", "company"])

    # Remove duplicate listings (same title + company)
    df = df.drop_duplicates(subset=["title", "company"])

    # Standardise column text
    df["title"] = df["title"].str.strip().str.title()
    df["company"] = df["company"].str.strip().str.title()
    df["location"] = df["location"].str.strip() if "location" in df.columns else "Ireland"

    # Classify job type
    df["job_type"] = df["title"].apply(classify_job_type)

    # Classify seniority
    df["seniority"] = df["title"].apply(classify_seniority)

    # Extract skills from summary
    df["skills_mentioned"] = df["summary"].apply(extract_skills)

    # Clean salary
    df["salary_clean"] = df["salary"].apply(clean_salary)

    log.info(f"Cleaned dataset: {len(df)} rows remaining")
    return df


def classify_job_type(title: str) -> str:
    title = str(title).lower()
    if any(x in title for x in ["intern", "internship", "graduate", "grad"]):
        return "Internship / Graduate"
    elif any(x in title for x in ["analyst"]):
        return "Data Analyst"
    elif any(x in title for x in ["scientist", "science"]):
        return "Data Scientist"
    elif any(x in title for x in ["engineer", "engineering"]):
        return "Data Engineer"
    elif any(x in title for x in ["bi ", "business intelligence", "power bi", "tableau"]):
        return "BI / Visualisation"
    else:
        return "Other"


def classify_seniority(title: str) -> str:
    title = str(title).lower()
    if any(x in title for x in ["intern", "internship", "junior", "graduate", "entry"]):
        return "Junior / Entry"
    elif any(x in title for x in ["senior", "sr.", "lead", "principal", "head"]):
        return "Senior"
    elif any(x in title for x in ["manager", "director", "vp", "chief"]):
        return "Manager / Director"
    else:
        return "Mid-Level"


def extract_skills(summary: str) -> str:
    """Find common data skills mentioned in job summaries."""
    if not summary:
        return ""
    summary = str(summary).lower()
    skills = [
        "python", "sql", "power bi", "tableau", "excel", "r ",
        "machine learning", "deep learning", "nlp", "spark",
        "azure", "aws", "gcp", "dbt", "airflow", "pandas",
        "scikit-learn", "tensorflow", "pytorch", "looker",
        "snowflake", "databricks", "kafka", "hadoop"
    ]
    found = [s.strip() for s in skills if s in summary]
    return ", ".join(found)


def clean_salary(salary: str) -> str:
    if not salary or salary == "Not specified":
        return "Not specified"
    # Keep only if it looks like a real salary
    if any(x in str(salary).lower() for x in ["€", "£", "k", "per", "year", "annual"]):
        return str(salary).strip()
    return "Not specified"


# ============================================================
# DATABASE STORAGE
# ============================================================

def save_to_sqlite(df: pd.DataFrame, db_path: str = DB_PATH):
    """Save cleaned job data to SQLite database."""
    conn = sqlite3.connect(db_path)
    df.to_sql("jobs", conn, if_exists="append", index=False)
    conn.close()
    log.info(f"Saved {len(df)} records to {db_path}")


def save_to_csv(df: pd.DataFrame):
    """Also save a CSV snapshot for Power BI import."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = f"data/processed/jobs_{timestamp}.csv"
    df.to_csv(path, index=False)
    log.info(f"CSV snapshot saved to {path}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():
    log.info("=" * 60)
    log.info("Ireland Job Market Scraper — Pipeline Starting")
    log.info("=" * 60)

    all_jobs = []

    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            log.info(f"Scraping Indeed.ie — '{term}' in '{location}'")
            indeed_jobs = scrape_indeed(term, location, pages=3)
            all_jobs.extend(indeed_jobs)

        log.info(f"Scraping Jobs.ie — '{term}'")
        jobsie_jobs = scrape_jobsie(term, pages=3)
        all_jobs.extend(jobsie_jobs)

    log.info(f"Total raw listings collected: {len(all_jobs)}")

    # Convert to DataFrame
    df = pd.DataFrame(all_jobs)

    # Clean
    df = clean_jobs(df)

    # Save
    save_to_sqlite(df)
    save_to_csv(df)

    log.info("Pipeline complete.")
    log.info(f"Final dataset: {len(df)} clean job listings")
    return df


if __name__ == "__main__":
    run_pipeline()
