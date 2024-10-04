from advanced_copilot.model.architecture.llama2_model import LLaMA2CodeCompletion
from typing import List, Optional

class SuggestionGenerator:
    def __init__(self, model_path: str, device: str):
        self.model = LLaMA2CodeCompletion(model_path, device)
        self.device = device

    def generate_completions(self, prompt: str, max_length: int = 50, num_suggestions: int = 5) -> List[str]:
        """Generates code completions using the language model.

        Args:
            prompt: The input text to generate completions from.
            max_length: The maximum length of the generated completions.
            num_suggestions: The number of completions to generate.

        Returns:
            A list of generated completions.

        Raises:
            ValueError: If `max_length` is non-positive or `num_suggestions` is non-positive.
            RuntimeError: If an error occurs during model generation.
        """

        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if num_suggestions <= 0:
            raise ValueError("num_suggestions must be positive")

        try:
            return self.model.generate(prompt, max_length=max_length, num_return_sequences=num_suggestions)
        except Exception as e:
            raise RuntimeError(f"Error generating completions: {e}")
