import heapq
from typing import List
import numpy as np

from pipeline.DatabaseInteractor import Neo4jInteractor


def cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two vectors with normalization,
    mimicking Neo4j's vector indexing behavior.

    Parameters:
    - vec1: list or np.ndarray, first vector
    - vec2: list or np.ndarray, second vector

    Returns:
    - float: cosine similarity score
    """
    # Ensure the vectors are NumPy arrays
    vec1 = np.array(vec1, dtype=float)
    vec2 = np.array(vec2, dtype=float)

    # Normalize vectors to unit length
    vec1 = vec1 / np.linalg.norm(vec1)
    vec2 = vec2 / np.linalg.norm(vec2)

    # Compute cosine similarity
    dot_product = np.dot(vec1, vec2)
    return 1 / 2 * (1 + dot_product)  # Equivalent to dot product after normalization


def ranking_chunks(
    interactor_database: Neo4jInteractor,
    chunks: list,
    question_vector: List[float] | list[List[float]],
    top_k: int,
    alpha: int = 40,
):
    score_embed_chunks = {}
    for chunk in chunks:
        score = cosine_similarity(question_vector, chunk["embedding"])
        score_embed_chunks[chunk["element_id"]] = score
    distances = interactor_database.calculate_distances(
        docs_id=[str(_["element_id"]) for _ in chunks], docs_id_ex=[]
    )

    chunks_score = {}
    for distance in distances:
        if distance["nodeA"] not in chunks_score:
            chunks_score[distance["nodeA"]] = score_embed_chunks[distance["nodeA"]]
        if distance["nodeB"] not in chunks_score:
            chunks_score[distance["nodeB"]] = score_embed_chunks[distance["nodeB"]]
        chunks_score[distance["nodeA"]] += (
            1
            / (distance["distance"] * distance["distance"] + alpha)
            * score_embed_chunks[distance["nodeB"]]
        )
        chunks_score[distance["nodeB"]] += (
            1
            / (distance["distance"] * distance["distance"] + alpha)
            * score_embed_chunks[distance["nodeA"]]
        )
    chunks_score = dict(
        sorted(chunks_score.items(), key=lambda item: item[1], reverse=True)
    )
    top_k_chunks = heapq.nlargest(top_k, chunks_score, key=chunks_score.get)
    print("Top k", top_k_chunks)
    return [chunk for chunk in chunks if chunk["element_id"] in top_k_chunks]
