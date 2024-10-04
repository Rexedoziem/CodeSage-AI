from advanced_copilot.model.architecture.llama2_model import LLaMA2CodeCompletion
from typing import List
import re
import ast

class CompletionFilter:
    def __init__(self, model: LLaMA2CodeCompletion):
        self.model = model

    def filter_completions(self, prompt: str, completions: List[str]) -> List[str]:
        filtered_completions = []
        for completion in completions:
            score = self.score_completion(prompt, completion)
            if score > 0:
                filtered_completions.append((completion, score))
        
        # Sort completions by score in descending order
        filtered_completions.sort(key=lambda x: x[1], reverse=True)
        
        # Return only the completions, without scores
        return [completion for completion, _ in filtered_completions]

    def score_completion(self, prompt: str, completion: str) -> float:
        score = 0.0
        
        # Check for syntax errors
        if self.is_valid_python(completion):
            score += 1.0
        else:
            return 0  # Discard completions with syntax errors

        # Check for relevance to the prompt
        if self.is_relevant(prompt, completion):
            score += 1.0

        # Check code style
        score += self.check_code_style(completion)

        # Check complexity
        score += self.check_complexity(completion)

        # Check for potential security issues
        if not self.has_security_issues(completion):
            score += 1.0

        return score

    def is_valid_python(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def is_relevant(self, prompt: str, completion: str) -> bool:
        # Simple relevance check: see if the completion contains keywords from the prompt
        prompt_keywords = set(re.findall(r'\w+', prompt.lower()))
        completion_keywords = set(re.findall(r'\w+', completion.lower()))
        return len(prompt_keywords.intersection(completion_keywords)) > 0

    def check_code_style(self, completion: str) -> float:
        score = 0.0
        
        # Check for proper indentation
        if all(line.startswith((' ' * 4, '\t')) for line in completion.splitlines() if line.strip()):
            score += 0.5

        # Check for appropriate naming conventions
        if re.search(r'\b[a-z_][a-z0-9_]*\b', completion):  # snake_case for variables and functions
            score += 0.5

        return score

    def check_complexity(self, completion: str) -> float:
        score = 0.0
        
        # Prefer shorter completions
        if len(completion) < 100:
            score += 0.5
        
        # Check for nested loops and conditionals
        ast_tree = ast.parse(completion)
        nested_depth = self.get_max_nested_depth(ast_tree)
        if nested_depth <= 2:
            score += 0.5

        return score

    def get_max_nested_depth(self, node, current_depth=0):
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If)):
                child_depth = self.get_max_nested_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def has_security_issues(self, completion: str) -> bool:
        # Check for potential security issues like use of eval() or exec()
        return any(func in completion for func in ['eval(', 'exec(', '__import__'])