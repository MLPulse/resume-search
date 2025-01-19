# data_ingestion.py

import os
import requests
import logging
import time
import csv
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load .env automatically (for ADZUNA_APP_ID, ADZUNA_APP_KEY, etc.)
load_dotenv()

logging.basicConfig(
    filename='data_ingestion.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdzunaFetcher:
    """
    Fetch jobs from Adzuna's public API.
    country_code can be 'us', 'ca', 'gb', etc. depending on region.
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
        """
        :param pages: Number of pages to fetch.
        :param results_per_page: Number of results per page.
        :param what: Keyword or job title (e.g. 'data engineer').
        :param where: Location query (e.g. 'New York').
        :return: A list of job postings from Adzuna.
        """
        all_jobs = []
        for page_num in range(1, pages + 1):
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

                    # Rate limit handling
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
                    break  # success, stop retry loop

                except requests.exceptions.RequestException as e:
                    logging.error(f"[Adzuna] Error p{page_num}, attempt {retries+1}: {e}")
                    if retries < max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        retries += 1
                    else:
                        logging.error("[Adzuna] Max retries reached, skipping this page.")
                        break
        return all_jobs

def normalize_adzuna_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an Adzuna job to a consistent schema for the 'resume search' project.
    """
    return {
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "description": job.get("description"),
        "url": job.get("redirect_url"),
        "source": "adzuna"
    }

def main():
    """
    Fetch from Adzuna (US), then save to CSV for deduplication & cleaning.
    """
    # 1. Instantiate
    adzuna_fetcher = AdzunaFetcher(country_code="us")
    
    # 2. Fetch job postings
    adzuna_raw = adzuna_fetcher.fetch_jobs(
        pages=2,
        results_per_page=5,
        what="data engineer",
        where="New York"
    )
    adzuna_jobs = [normalize_adzuna_job(j) for j in adzuna_raw]
    logging.info(f"Adzuna normalized jobs: {len(adzuna_jobs)}")

    # 3. Write the results to a CSV file
    fieldnames = ["title", "company", "location", "description", "url", "source"]
    with open("jobs.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for job in adzuna_jobs:
            writer.writerow(job)

    print(f"CSV file 'jobs.csv' written with {len(adzuna_jobs)} Adzuna rows.")

if __name__ == "__main__":
    main()