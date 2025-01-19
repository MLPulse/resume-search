# filtering.py

from typing import List, Dict, Optional
import re

def categorize_job(job: Dict) -> Dict:
    """
    Parse job fields (location, salary, remote vs. on-site, industry)
    and add standardized tags or typed fields for easier filtering.
    """
    
    updated_job = job.copy()

    # Standardize location
    location = job.get("location", "").strip().lower()
    if "remote" in location:
        updated_job["is_remote"] = True
    else:
        updated_job["is_remote"] = False

    # Standardize salary range
    raw_salary = job.get("salary_range", "").lower()
    if raw_salary:
        min_sal, max_sal = parse_salary_range(raw_salary)
        updated_job["min_salary"] = min_sal
        updated_job["max_salary"] = max_sal
    else:
        updated_job["min_salary"] = None
        updated_job["max_salary"] = None

    # Standardize industry
    industry = job.get("industry", "").strip().lower()
    updated_job["standardized_industry"] = industry

    # Standardize location
    updated_job["standardized_location"] = parse_location(location)

    return updated_job


def parse_salary_range(salary_str: str):
    """
    Basic parser for salary ranges. 
    Attempts to extract two numbers (min, max) from a string like '€50k - €70k' or '50000-70000'.
    Returns (min_salary, max_salary) as integers (annual).
    """
    
    # Replace 'k' with '000'
    salary_str = salary_str.replace("k", "000")
    # Remove currency symbols and punctuation except for hyphens
    salary_str = re.sub(r"[^\d\-]", "", salary_str)

    # Split on hyphens
    parts = salary_str.split("-")
    if len(parts) == 2:
        try:
            min_salary = int(parts[0])
            max_salary = int(parts[1])
            return min_salary, max_salary
        except ValueError:
            return None, None
    return None, None


def parse_location(location_str: str):
    """
    Very basic location parsing. If 'remote' is present, returns 'remote',
    else returns the part before a comma (if any).
    """
    if "remote" in location_str:
        return "remote"
    tokens = location_str.split(",")
    if tokens:
        return tokens[0].strip()
    return location_str  # fallback to raw


def categorize_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Categorize each job in the jobs list by calling 'categorize_job'.
    """
    return [categorize_job(job) for job in jobs]


def filter_by_location(jobs: List[Dict], location: str) -> List[Dict]:
    """
    Return jobs that match a given location (assumes standardized_location is set).
    """
    location_lower = location.strip().lower()
    return [job for job in jobs 
            if job.get("standardized_location", "").lower() == location_lower]


def filter_by_remote(jobs: List[Dict], remote: bool = True) -> List[Dict]:
    """
    Return jobs that are remote (if remote=True) or on-site (if remote=False).
    """
    return [job for job in jobs if job.get("is_remote", False) == remote]


def filter_by_salary_range(
    jobs: List[Dict], 
    min_salary: Optional[int] = None, 
    max_salary: Optional[int] = None
) -> List[Dict]:
    """
    Return jobs that fall within the specified salary range (inclusive).
    If min_salary or max_salary is None, treat them as unbounded on that side.
    """
    filtered = []
    for job in jobs:
        job_min = job.get("min_salary")
        job_max = job.get("max_salary")

        # Skip if no valid salary info
        if job_min is None or job_max is None:
            continue

        # Check lower bound
        if min_salary is not None and job_max < min_salary:
            continue
        # Check upper bound
        if max_salary is not None and job_min > max_salary:
            continue

        filtered.append(job)
    return filtered


def filter_by_industry(jobs: List[Dict], industry: str) -> List[Dict]:
    """
    Return jobs that match a given industry (assumes standardized_industry is set).
    """
    industry_lower = industry.strip().lower()
    return [job for job in jobs 
            if job.get("standardized_industry", "").lower() == industry_lower]