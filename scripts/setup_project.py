#!/usr/bin/env python3
import os
import subprocess

def create_directories(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

def create_readme():
    readme_content = """# Resume Search Project

This project aims to build an end-to-end ML/NLP pipeline for searching and ranking resumes.  

## Directory Structure
- **data_ingestion/**: Scripts and utilities to fetch or receive raw data.
- **data_processing/**: Code for cleaning, transforming, and preparing data.
- **models/**: Training scripts, saved model files, and related assets.
- **app/**: Main application code (APIs, UI, or any service endpoints).
- **tests/**: (Optional) Unit tests, integration tests, etc.

## Getting Started
1. Install dependencies (TBD).
2. Follow instructions in each subfolder.

Stay tuned for more details as we build this project step by step.
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Created README.md")

def create_gitignore():
    gitignore_content = """# Python cache and virtual env
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/
env/

# OS files
.DS_Store
Thumbs.db

# IDE settings (optional)
.vscode/
.idea/
"""
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("Created .gitignore")

def initialize_git_repo():
    try:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial project structure"], check=True)
        print("Initialized Git repository and made initial commit.")
    except Exception as e:
        print(f"Failed to initialize git repository: {e}")

if __name__ == "__main__":
    directories = ["data_ingestion", "data_processing", "models", "app", "tests"]
    create_directories(directories)
    create_readme()
    create_gitignore()
    initialize_git_repo()