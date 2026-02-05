from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self) -> None:
        model_name: str = "all-MiniLM-L6-v2"
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # model output dimension
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def generate_single_embeddings(self, text: str) -> List[float]:
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


