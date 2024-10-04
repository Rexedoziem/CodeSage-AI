from .user_model import UserModel
from ..architecture.llama2_model import LLaMA2CodeCompletion

class AdaptiveLearningManager:
    def __init__(self, base_model: LLaMA2CodeCompletion):
        self.base_model = base_model
        self.user_models = {}

    async def get_user_model(self, user_id: str) -> UserModel:
        if user_id not in self.user_models:
            self.user_models[user_id] = UserModel(user_id)
        return self.user_models[user_id]

    async def personalize_model(self, user_id: str) -> LLaMA2CodeCompletion:
        user_model = await self.get_user_model(user_id)
        personalized_embedding = user_model.get_personalized_embedding()

        # Create a copy of the base model to personalize
        personalized_model = self.base_model.copy()

        # Example: Parameter tuning
        for param in personalized_model.parameters():
            param.data += personalized_embedding  # Adjust parameters based on embedding

        return personalized_model

    async def update_user_model(self, user_id: str, code_snippet: str, accepted: bool):
        user_model = await self.get_user_model(user_id)
        if accepted:
            user_model.update_coding_patterns({"accepted_pattern": hash(code_snippet)})
        else:
            user_model.update_coding_patterns({"rejected_pattern": hash(code_snippet)})