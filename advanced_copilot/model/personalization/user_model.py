import torch
from typing import Dict

class UserModel:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences = {}
        self.coding_patterns = {}

    def update_preferences(self, new_preferences: Dict):
        self.preferences.update(new_preferences)

    def update_coding_patterns(self, new_patterns: Dict):
        self.coding_patterns.update(new_patterns)

    def get_personalized_embedding(self) -> torch.Tensor:
        embedding = torch.tensor([hash(f"{k}:{v}") for k, v in {**self.preferences, **self.coding_patterns}.items()])
        return embedding / embedding.norm()