# resume_parser.py

import os
import re
import pdfplumber
import docx
import spacy

def parse_pdf(file_path):
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
    return text

def parse_docx(file_path):
    """Extract text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {e}")
    return text

def tokenize_text(text):
    """
    Basic tokenizer that splits text into words, 
    removing punctuation and extra spaces.
    """
    tokens = re.split(r'[^a-zA-Z0-9]+', text)
    tokens = [token.strip() for token in tokens if token.strip()]
    return tokens

def load_spacy_model():
    """
    Load and return a spaCy language model.
    Make sure 'en_core_web_md' (or another model) is installed.
    """
    return spacy.load("en_core_web_md")

def is_potential_heading(line, max_words=5, uppercase_ratio=0.7):
    """
    Heuristic for deciding if a line might be a heading:
      - line length <= max_words
      - or line is mostly uppercase (ratio >= uppercase_ratio)
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    words = stripped.split()
    if len(words) <= max_words:
        return True

    upper_chars = sum(ch.isupper() for ch in stripped if ch.isalpha())
    total_alpha = sum(ch.isalpha() for ch in stripped)
    if total_alpha > 0:
        if (upper_chars / total_alpha) >= uppercase_ratio:
            return True

    return False

def get_section_label_with_score(line, nlp, synonyms_map, base_threshold=0.65):
    """
    Return both the best matching category and the best similarity score 
    for the given line, using spaCy embeddings.
    """
    line_doc = nlp(line.lower())
    best_category = "other"
    best_score = 0.0

    for category, synonyms in synonyms_map.items():
        for syn in synonyms:
            syn_doc = nlp(syn)
            score = line_doc.similarity(syn_doc)
            if score > best_score:
                best_score = score
                best_category = category
    
    if best_score >= base_threshold:
        return best_category, best_score
    else:
        return "other", best_score

def extract_sections_spacy(text, nlp):
    """
    Detect and separate 'education', 'experience', and 'skills' sections
    using spaCy similarity, short-line heading detection, 
    and a higher threshold to override the current section.
    """
    synonyms_map = {
        "education": [
            "education", "academic background", "academics", "schooling",
            "educational background", "bachelor", "master", "university",
            "college", "graduate studies"
        ],
        "experience": [
            "experience", "work history", "employment", 
            "professional experience", "career history"
        ],
        "skills": [
            "skills", "competencies", "expertise",
            "technical skills", "areas of expertise"
        ]
    }

    sections_dict = {
        "education": [],
        "experience": [],
        "skills": [],
        "other": []
    }
    
    current_section = "other"
    lines = text.split('\n')
    
    for line in lines:
        if is_potential_heading(line):
            predicted_category, best_score = get_section_label_with_score(line, nlp, synonyms_map, base_threshold=0.65)
            
            # If we found a valid heading (not 'other'), decide if we override current_section
            if predicted_category != "other":
                # If we're switching sections, require a higher threshold (0.75) 
                # to override the current section
                if current_section != predicted_category and best_score < 0.75:
                    # Not confident enough to override
                    sections_dict[current_section].append(line)
                    continue

                current_section = predicted_category
                continue
        
        # Otherwise it's content for the current section
        sections_dict[current_section].append(line)
    
    # Convert lists to strings
    for key, value in sections_dict.items():
        sections_dict[key] = "\n".join(value).strip()
    
    return sections_dict

def parse_resume(file_path):
    """
    Main function to parse a resume and return a structured dict
    with raw text, tokens, and basic section extraction (via spaCy).
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    raw_text = ""
    file_type = None

    if ext == ".pdf":
        raw_text = parse_pdf(file_path)
        file_type = "PDF"
    elif ext == ".docx":
        raw_text = parse_docx(file_path)
        file_type = "DOCX"
    else:
        print(f"Unsupported file type: {ext}")
        return None

    tokens = tokenize_text(raw_text)

    nlp = load_spacy_model()
    sections = extract_sections_spacy(raw_text, nlp)

    result = {
        "file_name": os.path.basename(file_path),
        "file_type": file_type,
        "raw_text": raw_text,
        "tokens": tokens,
        "sections": sections
    }

    return result

if __name__ == "__main__":
    sample_pdf = "test_resume.pdf"
    sample_docx = "test_resume.docx"

    pdf_data = parse_resume(sample_pdf)
    print("=== PDF Data ===")
    print(pdf_data)
    
    docx_data = parse_resume(sample_docx)
    print("\n=== DOCX Data ===")
    print(docx_data)