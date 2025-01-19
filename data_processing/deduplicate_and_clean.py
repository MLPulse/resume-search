import hashlib
import pandas as pd
import re
import html
import csv

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load raw job postings from a CSV file into a DataFrame.
    Uses Python engine to handle multiline CSV fields.
    """
    df = pd.read_csv(
        input_path,
        quotechar='"',
        escapechar='\\',
        sep=',',
        engine='python',
        on_bad_lines='warn'
    )
    return df

def clean_multiline_description(description: str) -> str:
    """
    Remove HTML tags/entities and unify multiline text into one line.
    """
    if not isinstance(description, str):
        return ""
    # Remove HTML tags, e.g., <b>, <br>, etc.
    no_tags = re.sub(r'<.*?>', '', description)
    # Decode common HTML entities (e.g., &nbsp;, &amp;, etc.)
    no_entities = html.unescape(no_tags)
    # Collapse multiple spaces or line breaks into one space
    single_line = ' '.join(no_entities.split())
    return single_line.strip()

def generate_hash(row: pd.Series, fields: list) -> str:
    """
    Generate a hash (MD5) for the row based on selected fields.
    """
    concat_str = '||'.join(
        str(row[field]).strip().lower()
        for field in fields
        if field in row and pd.notna(row[field])
    )
    return hashlib.md5(concat_str.encode('utf-8')).hexdigest()

def remove_duplicates(df: pd.DataFrame, fields_for_hash: list) -> pd.DataFrame:
    """
    Identify and remove duplicate rows based on a hash of key fields.
    By default, keeps the first occurrence.
    """
    df['row_hash'] = df.apply(lambda row: generate_hash(row, fields_for_hash), axis=1)
    df_dedup = df.drop_duplicates(subset=['row_hash'], keep='first').copy()
    df_dedup.drop(columns='row_hash', inplace=True)
    return df_dedup

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean or standardize fields in the DataFrame.
    """
    if 'title' in df.columns:
        df['title'] = df['title'].astype(str).apply(lambda x: x.strip().title())
    if 'company' in df.columns:
        df['company'] = df['company'].astype(str).apply(lambda x: x.strip())
    if 'location' in df.columns:
        df['location'] = df['location'].astype(str).apply(lambda x: x.strip())
    if 'description' in df.columns:
        df['description'] = df['description'].apply(clean_multiline_description)
    return df

def save_data(df: pd.DataFrame, output_path: str):
    """
    Save the cleaned DataFrame to a CSV file, quoting all fields
    to preserve punctuation or commas in text.
    """
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)

def main(input_csv: str, output_csv: str):
    """
    Main pipeline function:
      1. Load data (multiline-friendly)
      2. Clean multiline fields & remove HTML
      3. Deduplicate
      4. Save results
    """
    df = load_data(input_csv)
    df_clean = clean_data(df)
    fields_for_hash = ['title', 'company', 'location', 'description']
    df_dedup = remove_duplicates(df_clean, fields_for_hash)
    save_data(df_dedup, output_csv)
    print(f"Saved cleaned data to: {output_csv}")

# Example usage:
#if __name__ == "__main__":
#    main("jobs.csv", "cleaned_job_ads.csv")
