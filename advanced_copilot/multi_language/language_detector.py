import re
from typing import List, Dict
import os

class LanguageDetector:
    def __init__(self):
        self.language_patterns: Dict[str, re.Pattern] = {
            'python': re.compile(r'\.py$|^import\s+\w+|^from\s+\w+\s+import|^def\s+\w+\s*\(|^class\s+\w+:'),
            'javascript': re.compile(r'\.js$|^function\s+\w+\s*\(|^const\s+\w+\s*=|^let\s+\w+\s*=|^var\s+\w+\s*='),
            'java': re.compile(r'\.java$|^public\s+class\s+\w+|^private\s+\w+\s+\w+\s*\(|^protected\s+\w+\s+\w+\s*\('),
            'ruby': re.compile(r'\.rb$|^require\s+|^def\s+\w+\s*(\(|$)|^class\s+\w+\s*(<|\n)'),
            'go': re.compile(r'\.go$|^package\s+\w+|^func\s+\w+\s*\(|^type\s+\w+\s+struct'),
            'rust': re.compile(r'\.rs$|^fn\s+\w+\s*\(|^let\s+mut\s+\w+|^impl\s+\w+\s+for'),
        }

    def detect_language(self, code_file: str) -> str:
        if os.path.isfile(code_file):
            with open(code_file, 'r') as file:
                code = file.read()
            # Check file extension first
            _, file_extension = os.path.splitext(code_file)
            for lang, pattern in self.language_patterns.items():
                if pattern.search(file_extension):
                    return lang
        else:
            code = code_file

        code = self._preprocess_code(code)
        scores = {lang: 0 for lang in self.language_patterns}
        for lang, pattern in self.language_patterns.items():
            matches = pattern.findall(code)
            scores[lang] = len(matches)
        detected_lang = max(scores, key=scores.get)
        return detected_lang if scores[detected_lang] > 0 else 'unknown'

    def _preprocess_code(self, code: str) -> str:
        # Remove comments (this is a simple approach and might not cover all cases)
        code = re.sub(r'#.*|//.*|/\*[\s\S]*?\*/', '', code)
        # Remove string literals (again, a simple approach)
        code = re.sub(r'".*?"|\'.*?\'', '', code)
        return code

    def get_supported_languages(self) -> List[str]:
        return list(self.language_patterns.keys())