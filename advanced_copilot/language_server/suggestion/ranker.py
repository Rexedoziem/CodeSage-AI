import torch
from typing import List, Tuple
from advanced_copilot.model.architecture.llama2_model import LLaMA2CodeCompletion

class CompletionRanker:
    def __init__(self, model: LLaMA2CodeCompletion):
        self.model = model

    def rank_completions(self, prompt: str, completions: List[str]) -> List[Tuple[str, float]]:
        ranked_completions = []

        for completion in completions:
            # Tokenize the prompt and completion together
            input_ids = self.model.tokenizer.encode(prompt + completion, return_tensors="pt", clean_up_tokenization_spaces=False)
            # Move input to the same device as the model
            input_ids = input_ids.to(self.model.model.device)

            # Generate logits for the entire sequence
            with torch.no_grad():
                outputs = self.model.model(input_ids)
                logits = outputs.logits

            # Calculate the likelihood of the completion
            completion_ids = self.model.tokenizer.encode(completion, add_special_tokens=False, clean_up_tokenization_spaces=False)
            completion_logits = logits[0, -len(completion_ids):, :]
            completion_log_probs = torch.log_softmax(completion_logits, dim=-1)

            # Calculate the average log probability of the completion tokens
            completion_token_ids = torch.tensor(completion_ids).to(self.model.model.device)
            completion_token_log_probs = completion_log_probs[torch.arange(len(completion_ids)), completion_token_ids]
            avg_log_prob = completion_token_log_probs.mean().item()

            # Convert log probability to a score (you can use exp() if you want the actual probability)
            score = avg_log_prob

            ranked_completions.append((completion, score))

        # Sort completions by score in descending order
        return sorted(ranked_completions, key=lambda x: x[1], reverse=True)