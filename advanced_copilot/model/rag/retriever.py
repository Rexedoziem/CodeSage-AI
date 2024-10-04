import faiss
import numpy as np
from typing import List, Tuple
import config
from .embeddings import CodeEmbedding

class CodeRetriever:
    def __init__(self):
        self.embedding_model = CodeEmbedding()
        self.index = faiss.IndexFlatL2(config.EMBEDDING_DIMENSION)
        self.code_snippets = []

    def add_code(self, code_snippets: List[str]):
        embeddings = [self.embedding_model.encode(code) for code in code_snippets]
        self.index.add(np.array(embeddings))
        self.code_snippets.extend(code_snippets)

    def retrieve(self, query: str, k: int = config.RETRIEVAL_TOP_K) -> List[Tuple[str, float]]:
        query_embedding = self.embedding_model.encode(query)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return [(self.code_snippets[i], distances[0][j]) for j, i in enumerate(indices[0])]