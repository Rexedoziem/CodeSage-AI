from typing import Dict, List
from pylsp.workspace import Document
from pylsp.position import Position
import ast

class ContextAnalyzer:
    def analyze(self, document: Document, position: Position) -> Dict:
        context = {
            'user_id': 'example_user_id',  # This should be obtained from the client
            'code': document.source,
            'language': document.language_id,
            'position': {
                'line': position.line,
                'character': position.character
            },
        }

        # Parse the AST
        tree = ast.parse(document.source)

        # Find the node at the current position
        node = self.find_node_at_position(tree, position)

        if node:
            context['current_node'] = {
                'type': type(node).__name__,
                'line': node.lineno,
                'col': node.col_offset
            }

            # Get the surrounding context
            context['surrounding_code'] = self.get_surrounding_code(document, position)

            # Analyze imports
            context['imports'] = self.analyze_imports(tree)

            # Analyze function context
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                context['function_context'] = self.analyze_function(node)
            elif isinstance(node, ast.ClassDef):
                context['class_context'] = self.analyze_class(node)

        return context

    def find_node_at_position(self, tree: ast.AST, position: Position) -> ast.AST:
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
                if node.lineno == position.line + 1 and node.col_offset <= position.character:
                    return node
        return None

    def get_surrounding_code(self, document: Document, position: Position, context_lines: int = 2) -> str:
        lines = document.lines
        start = max(0, position.line - context_lines)
        end = min(len(lines), position.line + context_lines + 1)
        return '\n'.join(lines[start:end])

    def analyze_imports(self, tree: ast.AST) -> List[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{', '.join(alias.name for alias in node.names)}")
        return imports

    def analyze_function(self, node: ast.FunctionDef) -> Dict:
        return {
            'name': node.name,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [self.get_decorator_name(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        }

    def analyze_class(self, node: ast.ClassDef) -> Dict:
        return {
            'name': node.name,
            'bases': [self.get_name(base) for base in node.bases],
            'methods': [method.name for method in node.body if isinstance(method, ast.FunctionDef)],
            'docstring': ast.get_docstring(node)
        }

    def get_decorator_name(self, decorator: ast.expr) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self.get_name(decorator.func)
        return str(decorator)

    def get_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        return str(node)