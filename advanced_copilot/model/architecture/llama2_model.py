import torch
from typing import List
from transformers import AutoModelForCausalLM, AutoTokenizer

class LLaMA2CodeCompletion:
    def __init__(self, model_path: str, device: str):
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.device = device

    async def generate(self, prompt: str, max_length: int = 50, num_return_sequences: int = 1) -> List[str]:
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        outputs = self.model.generate(
            input_ids,
            max_length=input_ids.shape[1] + max_length,
            num_return_sequences=num_return_sequences,
            do_sample=True,
            top_p=0.95,
            top_k=50,
        )
        
        return [self.tokenizer.decode(seq[input_ids.shape[1]:], skip_special_tokens=True) for seq in outputs]

    async def generate_stream(self, prompt: str, max_length: int = 50, num_return_sequences: int = 1):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        for i in range(max_length):
            outputs = self.model.generate(
                input_ids,
                max_length=input_ids.shape[1] + 1,
                num_return_sequences=num_return_sequences,
                do_sample=True,
                top_p=0.95,
                top_k=50,
            )
            
            for seq in outputs:
                yield self.tokenizer.decode(seq[input_ids.shape[1]:], skip_special_tokens=True)
            
            input_ids = outputs[:, :input_ids.shape[1]+1]