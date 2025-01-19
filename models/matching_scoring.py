import numpy as np

def compute_cosine_similarity(vector_a, vector_b):
    """
    Compute the cosine similarity between two vectors.
    
    Args:
        vector_a (np.ndarray): The first vector.
        vector_b (np.ndarray): The second vector.
    
    Returns:
        float: The cosine similarity score between vector_a and vector_b.
               Returns 0.0 if either vector is zero-length.
    """
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    
    similarity = np.dot(vector_a, vector_b) / (norm_a * norm_b)
    return float(similarity)

def match_resume_to_jobs(resume_vector, job_vectors, top_n=5, store_results=False,
                         storage_dict=None, resume_id=None):
    """
    Given a single resume_vector and a list of (job_id, job_vector) pairs, 
    compute cosine similarity and return the top N matches with their scores.
    
    Optionally, store or retrieve these scores in a storage dictionary.
    
    Args:
        resume_vector (np.ndarray): The vector representation of the résumé.
        job_vectors (list): A list of (job_id, job_vector) tuples.
        top_n (int): Number of top matches to return.
        store_results (bool): If True, store the computed results in storage_dict.
        storage_dict (dict): A dictionary for storing/retrieving results by resume_id.
        resume_id (hashable): Unique identifier for this résumé (e.g., string or int).
        
    Returns:
        list: Sorted list (descending) of top N (job_id, similarity_score) pairs.
    """
    
    # If we already have scores for this resume, return them directly
    if storage_dict is not None and resume_id is not None:
        if resume_id in storage_dict:
            existing_scores = storage_dict[resume_id]
            return sorted(existing_scores, key=lambda x: x[1], reverse=True)[:top_n]
    
    # Otherwise, compute new similarity scores
    scores = []
    for job_id, job_vec in job_vectors:
        score = compute_cosine_similarity(resume_vector, job_vec)
        scores.append((job_id, score))
    
    # Sort in descending order of similarity
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Store the full list of results if requested
    if store_results and storage_dict is not None and resume_id is not None:
        storage_dict[resume_id] = scores
    
    return scores[:top_n]

# if __name__ == "__main__":
#     # Example usage
#     resume_vec = np.array([1, 2, 3])
#     job_vectors = [
#         ("job1", np.array([1, 1, 1])),
#         ("job2", np.array([2, 2, 1])),
#         ("job3", np.array([0, 0, 0]))
#     ]
#     storage = {}
#     top_jobs = match_resume_to_jobs(resume_vec, job_vectors, top_n=2, 
#                                     store_results=True, storage_dict=storage, resume_id="resume123")
#     print("Top Matches:", top_jobs)
#     # Then retrieving
#     cached_results = match_resume_to_jobs(resume_vec, job_vectors, top_n=2, 
#                                         store_results=True, storage_dict=storage, resume_id="resume123")
#     print("Cached Matches:", cached_results)