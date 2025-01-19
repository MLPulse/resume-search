# data_processing.py

import spacy
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import AutoTokenizer, AutoModel
import torch

nlp = spacy.load("en_core_web_md")

def clean_text(text: str, lemmatize: bool = True) -> str:
    """
    Clean the input text by lowercasing, removing stopwords, punctuation, and optionally lemmatizing.

    :param text: The raw text.
    :param lemmatize: Flag to perform lemmatization if True.
    :return: Cleaned text.
    """
    doc = nlp(text.lower())
    cleaned_tokens = []

    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        if lemmatize:
            cleaned_tokens.append(token.lemma_)
        else:
            cleaned_tokens.append(token.text)

    return " ".join(cleaned_tokens)


class DataProcessor:
    def __init__(self, lemmatize: bool = True):
        """
        Initialize the DataProcessor with optional lemmatization.

        :param lemmatize: Whether to apply lemmatization during text cleaning.
        """
        self.lemmatize = lemmatize
        self.tfidf_vectorizer = None
        self.tokenizer = None
        self.model = None

    def fit_tfidf(self, texts: List[str]):
        """
        Fit the TF-IDF vectorizer on the given texts.

        :param texts: A list of raw documents (strings).
        """
        cleaned_texts = [clean_text(t, self.lemmatize) for t in texts]
        self.tfidf_vectorizer = TfidfVectorizer()
        self.tfidf_vectorizer.fit(cleaned_texts)

    def transform_tfidf(self, texts: List[str]):
        """
        Transform texts to TF-IDF vectors based on a fitted vectorizer.

        :param texts: A list of raw documents (strings).
        :return: A TF-IDF feature matrix (scipy sparse format).
        """
        if not self.tfidf_vectorizer:
            raise ValueError("TF-IDF vectorizer not fitted. Call fit_tfidf first.")
        cleaned_texts = [clean_text(t, self.lemmatize) for t in texts]
        return self.tfidf_vectorizer.transform(cleaned_texts)

    def load_bert_model(self, model_name: str = "bert-base-uncased"):
        """
        Load a pretrained BERT model from Hugging Face.

        :param model_name: The Hugging Face model name.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def get_bert_embedding(self, text: str) -> torch.Tensor:
        """
        Generate a BERT embedding for a single piece of text.

        :param text: Raw text input.
        :return: A torch.Tensor representing the CLS embedding (shape: [hidden_size]).
        """
        if not self.tokenizer or not self.model:
            raise ValueError("BERT model not loaded. Call load_bert_model first.")
        
        cleaned_text = clean_text(text, self.lemmatize)
        inputs = self.tokenizer(cleaned_text, return_tensors="pt", truncation=True, padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        last_hidden_state = outputs.last_hidden_state
        cls_embedding = last_hidden_state[:, 0, :]
        return cls_embedding.squeeze(0)

    def get_bert_embeddings(self, texts: List[str]) -> torch.Tensor:
        """
        Generate BERT embeddings for a list of text strings.

        :param texts: A list of raw text inputs.
        :return: A torch.Tensor of shape [num_texts, hidden_size].
        """
        if not self.tokenizer or not self.model:
            raise ValueError("BERT model not loaded. Call load_bert_model first.")

        all_embeddings = []
        for txt in texts:
            emb = self.get_bert_embedding(txt)
            all_embeddings.append(emb.unsqueeze(0))

        return torch.cat(all_embeddings, dim=0)

# Example usage:
# if __name__ == "__main__":
#     sample_texts = [
#         "Senior Data Scientist with 5 years of experience in machine learning.",
#         "Looking for a Data Scientist to build predictive models."
#     ]
#     processor = DataProcessor(lemmatize=True)

#     # TF-IDF
#     processor.fit_tfidf(sample_texts)
#     tfidf_vectors = processor.transform_tfidf(sample_texts)
#     print("TF-IDF shape:", tfidf_vectors.shape)

#     # BERT
#     processor.load_bert_model("bert-base-uncased")
#     bert_vectors = processor.get_bert_embeddings(sample_texts)
#     print("BERT shape:", bert_vectors.shape)
