import ast
import sys
import subprocess
import inspect
import tempfile
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    issue_type: str
    description: str
    line_number: int
    column: int

class CodeAnalyzer:
    def __init__(self):
        self.unsafe_functions = {
            'eval': 'Evaluates a string as Python code',
            'exec': 'Executes Python code dynamically',
            #'pickle.loads': 'Deserializes potentially malicious data',
            #'subprocess.call': 'Executes system commands',
            #'os.system': 'Executes system commands',
        }
        self.unsafe_modules = {
            'pickle': 'Potentially unsafe serialization',
            #'subprocess': 'Allows execution of system commands',
            #'os': 'Provides access to operating system functions',
        }
        self.dynamic_issues = []

    def analyze_security(self, code: str) -> List[SecurityIssue]:
        static_issues = self._static_analysis(code)
        dynamic_issues = self._dynamic_analysis(code)
        bandit_issues = self._bandit_analysis(code)
        return static_issues + dynamic_issues + bandit_issues

    def _static_analysis(self, code: str) -> List[SecurityIssue]:
        tree = ast.parse(code)
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_function_call(node, issues)
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                self._check_import(node, issues)
            elif isinstance(node, ast.Assign):
                self._check_assignment(node, issues)

        return issues

    def _check_function_call(self, node: ast.Call, issues: List[SecurityIssue]):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.unsafe_functions:
                issues.append(SecurityIssue(
                    "Unsafe Function Call",
                    f"Potentially unsafe use of '{func_name}': {self.unsafe_functions[func_name]}",
                    node.lineno,
                    node.col_offset
                ))
        elif isinstance(node.func, ast.Attribute):
            full_name = f"{self._get_attribute_name(node.func)}.{node.func.attr}"
            if full_name in self.unsafe_functions:
                issues.append(SecurityIssue(
                    "Unsafe Function Call",
                    f"Potentially unsafe use of '{full_name}': {self.unsafe_functions[full_name]}",
                    node.lineno,
                    node.col_offset
                ))

    def _check_import(self, node: ast.Import | ast.ImportFrom, issues: List[SecurityIssue]):
        for alias in node.names:
            if alias.name in self.unsafe_modules:
                issues.append(SecurityIssue(
                    "Unsafe Module Import",
                    f"Importing potentially unsafe module '{alias.name}': {self.unsafe_modules[alias.name]}",
                    node.lineno,
                    node.col_offset
                ))

    def _check_assignment(self, node: ast.Assign, issues: List[SecurityIssue]):
        if isinstance(node.value, ast.Str) and len(node.value.s) > 100:
            issues.append(SecurityIssue(
                "Large String Assignment",
                "Assignment of a large string literal. Could potentially contain encoded malicious code.",
                node.lineno,
                node.col_offset
            ))

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return ""

    def _dynamic_analysis(self, code: str) -> List[SecurityIssue]:
        self.dynamic_issues = []
        
        def trace_calls(frame, event, arg):
            if event != 'call':
                return
            co = frame.f_code
            func_name = co.co_name
            if func_name in self.unsafe_functions:
                # Get the source lines of the current frame
                try:
                    lines, start_line = inspect.getsourcelines(frame)
                    # The column is the first non-whitespace character
                    column = len(lines[frame.f_lineno - start_line]) - len(lines[frame.f_lineno - start_line].lstrip())
                except Exception:
                    column = 0  # Fallback if we can't get the source

                self.dynamic_issues.append(SecurityIssue(
                    "Unsafe Function Call (Runtime)",
                    f"Potentially unsafe use of '{func_name}': {self.unsafe_functions[func_name]}",
                    frame.f_lineno,
                    column,
                    frame.f_code.co_name  # Include the name of the function where the issue was found
                ))
            return trace_calls

        sys.settrace(trace_calls)
        try:
            exec(code)
        except Exception as e:
            print(f"Error during dynamic analysis: {e}")
        finally:
            sys.settrace(None)

        return self.dynamic_issues

    def _bandit_analysis(self, code: str) -> List[SecurityIssue]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name

        result = subprocess.run(['bandit', '-f', 'json', temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        issues = []

        if result.returncode == 0:
            output = result.stdout.decode()
            issues.extend(self._parse_bandit_output(output))
        else:
            error_message = result.stderr.decode()
            issues.append(SecurityIssue(
                "Bandit Error",
                f"Error running Bandit: {error_message}",
                0,
                0
            ))

        return issues

    def _parse_bandit_output(self, output: str) -> List[SecurityIssue]:
        import json
        issues = []
        try:
            bandit_result = json.loads(output)
            for result in bandit_result.get('results', []):
                issues.append(SecurityIssue(
                    "Bandit Issue",
                    result['issue_text'],
                    result['line_number'],
                    0  # Bandit does not provide column information
                ))
        except json.JSONDecodeError:
            issues.append(SecurityIssue(
                "Bandit Parsing Error",
                "Error parsing Bandit output",
                0,
                0
            ))
        return issues

    def generate_report(self, issues: List[SecurityIssue]) -> str:
        if not issues:
            return "No security issues found."

        report = "Security Analysis Report:\n\n"
        for i, issue in enumerate(issues, 1):
            report += f"{i}. {issue.issue_type} (Line {issue.line_number}, Column {issue.column}):\n"
            report += f"   {issue.description}\n\n"

        report += f"Total issues found: {len(issues)}"
        return report

