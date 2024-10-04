from sentence_transformers import SentenceTransformer
import torch
import config

class CodeEmbedding:
    def __init__(self):
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)

    def encode(self, code: str) -> torch.Tensor:
        return self.model.encode(code, convert_to_tensor=True)