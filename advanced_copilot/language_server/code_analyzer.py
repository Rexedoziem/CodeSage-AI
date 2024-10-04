from typing import List, Dict
import ast
import tempfile
import subprocess
import astroid
#from pylint import epylint as lint
from pyflakes.api import check as pyflakes_check
from pycodestyle import Checker as PEP8Checker
from advanced_copilot.multi_language.language_detector import LanguageDetector
from advanced_copilot.language_server.security.code_analyzer import CodeAnalyzer

class CodeAnalyzer:
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.security_analyzer = CodeAnalyzer()

    def analyze_code(self, code: str, file_path: str) -> Dict[str, List[Dict]]:
        language = self.language_detector.detect_language(code)
        issues = {
            "errors": [],
            "warnings": [],
            "style_issues": [],
            "security_issues": []
        }

        if language == "python":
            issues = self._analyze_python(code, file_path, issues)
        elif language == "javascript":
            issues = self._analyze_javascript(code, file_path, issues)
        elif language == "java":
            issues = self._analyze_java(code, file_path, issues)
        
        # Add security analysis for all languages
        security_issues = self.security_analyzer.analyze(code, language)
        issues["security_issues"].extend(security_issues)

        return issues

    def _analyze_python(self, code: str, file_path: str, issues: Dict) -> Dict:
        # AST analysis
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues["errors"].append({
                "line": e.lineno,
                "column": e.offset,
                "message": str(e)
            })

        # Pylint analysis
        pylint_stdout, pylint_stderr = lint.py_run(file_path, return_std=True)
        pylint_issues = pylint_stdout.getvalue().split("\n")
        for issue in pylint_issues:
            if issue.startswith("E:"):
                issues["errors"].append(self._parse_pylint_issue(issue))
            elif issue.startswith("W:"):
                issues["warnings"].append(self._parse_pylint_issue(issue))

        # Pyflakes analysis
        pyflakes_issues = pyflakes_check(code.encode(), file_path)
        for issue in pyflakes_issues:
            issues["warnings"].append({
                "line": issue.lineno,
                "column": issue.col,
                "message": issue.message
            })

        # PEP8 analysis
        pep8_checker = PEP8Checker(file_path)
        for line_number, offset, code, text, _ in pep8_checker.check_all():
            issues["style_issues"].append({
                "line": line_number,
                "column": offset + 1,
                "message": f"{code}: {text}"
            })

        return issues

    def _analyze_javascript(self, code: str, file_path: str, issues: Dict) -> Dict:
        # Create a temporary file to store the JavaScript code
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as temp_file:
            temp_file.write(code.encode("utf-8"))

        # Run ESLint on the temporary file
        result = subprocess.run(["eslint", temp_file.name], capture_output=True, text=True)

        # Parse the ESLint output and add issues to the dictionary
        for line in result.stdout.splitlines():
            line_number, column, message = line.split(":")
            issues["warnings"].append({
                "line": int(line_number),
                "column": int(column),
                "message": message.strip()
            })

        return issues

    def _analyze_java(self, code: str, file_path: str, issues: Dict) -> Dict:
        # Create a temporary file to store the Java code
        with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as temp_file:
            temp_file.write(code.encode("utf-8"))

        # Run CheckStyle on the temporary file (replace with your CheckStyle configuration file)
        result = subprocess.run(["checkstyle", "-c", "checkstyle.xml", temp_file.name], capture_output=True, text=True)

        # Parse the CheckStyle output and add issues to the dictionary
        for line in result.stdout.splitlines():
            if line.startswith("ERROR") or line.startswith("WARNING"):
                parts = line.split(":")
                line_number = int(parts[1])
                column_number = int(parts[2])
                message = parts[3].strip()
                issue = {
                    "line": line_number,
                    "column": column_number,
                    "message": message
                }
                issues["warnings"].append(issue)

        return issues

    def _parse_pylint_issue(self, issue: str) -> Dict:
        parts = issue.split(":")
        return {
            "line": int(parts[1]),
            "column": int(parts[2]),
            "message": parts[3].strip()
        }