# data_ingestion.py

import os
import requests
import logging
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv() 

logging.basicConfig(
    filename='data_ingestion.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdzunaFetcher:
    """
    Fetch jobs from Adzuna's public API.
    """
    def __init__(self, country_code: str = "us"):
        self.app_id = os.environ.get("ADZUNA_APP_ID", "YOUR_ADZUNA_APP_ID")
        self.app_key = os.environ.get("ADZUNA_APP_KEY", "YOUR_ADZUNA_APP_KEY")
        self.country_code = country_code
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{self.country_code}/search"

    def fetch_jobs(
        self,
        pages: int = 1,
        results_per_page: int = 10,
        what: Optional[str] = None,
        where: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        all_jobs = []
        for page_num in range(1, pages + 1):
            # Basic rate-limit handling variables
            backoff = 30
            max_retries = 3
            retries = 0

            while retries <= max_retries:
                try:
                    url = f"{self.base_url}/{page_num}"
                    params = {
                        "app_id": self.app_id,
                        "app_key": self.app_key,
                        "results_per_page": results_per_page
                    }
                    if what:
                        params["what"] = what
                    if where:
                        params["where"] = where

                    logging.info(f"[Adzuna] Page {page_num}, Attempt {retries+1}, Params: {params}")
                    response = requests.get(url, params=params)

                    # If 429, back off
                    if response.status_code == 429:
                        logging.warning(f"[Adzuna] Rate limit. Sleeping {backoff}s...")
                        time.sleep(backoff)
                        backoff *= 2
                        retries += 1
                        continue

                    response.raise_for_status()
                    data = response.json()
                    jobs = data.get("results", [])
                    logging.info(f"[Adzuna] Got {len(jobs)} jobs from page {page_num}")
                    all_jobs.extend(jobs)
                    break  # success

                except requests.exceptions.RequestException as e:
                    logging.error(f"[Adzuna] Error p{page_num}, attempt {retries+1}: {e}")
                    if retries < max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        retries += 1
                    else:
                        logging.error("[Adzuna] Max retries reached, skipping.")
                        break
        return all_jobs

class JoobleFetcher:
    """
    Fetch jobs from Jooble's public API.
    """
    def __init__(self):
        self.api_key = os.environ.get("JOOBLE_API_KEY", "YOUR_JOOBLE_API_KEY")
        self.base_url = "https://jooble.org/api"

    def fetch_jobs(
        self,
        pages: int = 1,
        results_per_page: int = 10,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        all_jobs = []
        offset = 0
        for _ in range(pages):
            backoff = 30
            max_retries = 3
            retries = 0

            payload = {
                "keywords": keywords if keywords else "",
                "location": location if location else "",
                "page": offset,
                "limit": results_per_page
            }

            while retries <= max_retries:
                try:
                    url = f"{self.base_url}/{self.api_key}"
                    logging.info(f"[Jooble] Offset={offset}, Attempt {retries+1}, Payload: {payload}")
                    response = requests.post(url, json=payload)

                    if response.status_code == 429:
                        logging.warning(f"[Jooble] Rate limit. Sleeping {backoff}s...")
                        time.sleep(backoff)
                        backoff *= 2
                        retries += 1
                        continue

                    response.raise_for_status()
                    data = response.json()
                    jobs = data.get("jobs", [])
                    logging.info(f"[Jooble] Got {len(jobs)} jobs at offset={offset}")
                    all_jobs.extend(jobs)
                    break  # success

                except requests.exceptions.RequestException as e:
                    logging.error(f"[Jooble] Error offset={offset}, attempt {retries+1}: {e}")
                    if retries < max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        retries += 1
                    else:
                        logging.error("[Jooble] Max retries reached, skipping.")
                        break

            offset += results_per_page

        return all_jobs

def normalize_adzuna_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an Adzuna job to a common schema for the resume search project.
    """
    return {
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "description": job.get("description"),
        "url": job.get("redirect_url"),
        "source": "adzuna"
    }

def normalize_jooble_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Jooble job to a common schema for the resume search project.
    """
    return {
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "description": job.get("snippet"),
        "url": job.get("link"),
        "source": "jooble"
    }

def main():
    """
    Demonstration usage for Prompt 2: Data Ingestion & Scraping.
    """
    # Fetch from Adzuna
    adzuna_fetcher = AdzunaFetcher(country_code="us")
    adzuna_raw = adzuna_fetcher.fetch_jobs(
        pages=1,
        results_per_page=5,
        what="data engineer",
        where="New York"
    )
    adzuna_jobs = [normalize_adzuna_job(j) for j in adzuna_raw]
    logging.info(f"Adzuna normalized jobs: {len(adzuna_jobs)}")

    # Fetch from Jooble
    jooble_fetcher = JoobleFetcher()
    jooble_raw = jooble_fetcher.fetch_jobs(
        pages=1,
        results_per_page=5,
        keywords="data engineer",
        location="New York"
    )
    jooble_jobs = [normalize_jooble_job(j) for j in jooble_raw]
    logging.info(f"Jooble normalized jobs: {len(jooble_jobs)}")

    # Combine results
    combined_jobs = adzuna_jobs + jooble_jobs
    print(f"Total combined job postings: {len(combined_jobs)}")
    if combined_jobs:
        print("Sample job:", combined_jobs[0])

if __name__ == "__main__":
    main()