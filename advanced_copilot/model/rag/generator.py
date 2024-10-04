from typing import List, Generator
from .retriever import CodeRetriever
from ..architecture.llama2_model import LLaMA2CodeCompletion

class RAGCodeCompletion:
    def __init__(self):
        self.retriever = CodeRetriever()
        self.generator = LLaMA2CodeCompletion()

    def generate_stream(self, query: str, max_length: int = 50) -> Generator[str, None, None]:
        retrieved_codes = self.retriever.retrieve(query)
        context = "\n".join([code for code, _ in retrieved_codes])
        prompt = f"{context}\n\n{query}"
        
        yield from self.generator.generate_stream(prompt, max_length)

    def add_code_to_retriever(self, code_snippets: List[str]):
        self.retriever.add_code(code_snippets)