from typing import List, Tuple

class ErrorFixer:
    def suggest_fixes(self, errors: List[Tuple[str, int, str]], code: str) -> List[Tuple[str, str]]:
        fixes = []
        lines = code.split('\n')
        
        for error, lineno, offset in errors:
            if "SyntaxError" in error:
                # For syntax errors, suggest based on common mistakes
                if "EOF while scanning" in error:
                    fixes.append((error, "Check for unclosed parentheses, brackets, or quotes"))
                elif "invalid syntax" in error:
                    fixes.append((error, "Review the line for typos or missing colons"))
            elif "Empty except clause" in error:
                fixes.append((error, f"Add a specific exception to catch on line {lineno}"))
            elif "Bare except clause" in error:
                fixes.append((error, f"Specify an exception to catch on line {lineno}, e.g., 'except Exception:'"))
            
        return fixes