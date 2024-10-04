import asyncio
from pylsp import uris
from pylsp.config import config
from pylsp.workspace import Document
from pylsp.python_lsp import PythonLSPServer
from typing import Optional, Dict, List
from completion_provider import CompletionProvider
from advanced_copilot.model.rag.retriever import CodeRetriever
import config
from advanced_copilot.model.architecture.llama2_model import LLaMA2CodeCompletion
from io import StringIO  # Import StringIO from the io module

class CopilotLanguageServer(PythonLSPServer):
    def __init__(self, rx, tx):
        super().__init__(rx, tx)
        # Initialize these with proper paths and models
        self.retriever = CodeRetriever()  
        self.completion_provider = CompletionProvider('Rexe/llama-3.1-codegen-merged', device='cpu')

    def capabilities(self):
        return {
            'textDocumentSync': {
                'change': 2,
                'save': {
                    'includeText': False
                },
                'openClose': True,
            },
            'completionProvider': {
                'triggerCharacters': ['.']
            }
        }

    async def completions(self, params: Dict) -> List[Dict]:
        uri = params['textDocument']['uri']
        position = params['position']
        doc = self.workspace.get_document(uri)
        
        user_id = self.get_user_id(doc)
        code_context = self.get_code_context(doc, position)

        completions = []
        async for completion, language in self.completion_provider.get_completions(
            user_id=user_id,
            code_context=code_context
        ):
            completions.append({
                'label': completion,
                'kind': 15,  # Snippet
                'detail': f'Copilot suggestion ({language})',
                'insertText': completion
            })
        return completions

    def get_user_id(self, document: Document) -> str:
        # Method 1: From workspace configuration
        config = self.workspace.get_configuration(document.uri)
        user_id = config.get('userId')
        if user_id:
            return user_id

        # Method 2: From environment variable
        import os
        user_id = os.environ.get('LSP_USER_ID')
        if user_id:
            return user_id

        # Method 3: From a file in the workspace
        from pathlib import Path
        workspace_root = Path(uris.to_fs_path(document.uri)).parent
        user_id_file = workspace_root / '.lsp_user_id'
        if user_id_file.exists():
            with open(user_id_file, 'r') as f:
                return f.read().strip()

        # Fallback: Use document path as a simple user ID
        return document.path

    def get_code_context(self, document: Document, position: Dict) -> str:
        # Get all lines up to the current position
        lines = document.lines[:position['line'] + 1]
        
        # For the current line, only include up to the cursor position
        lines[-1] = lines[-1][:position['character']]
        
        return '\n'.join(lines)

# Mock rx and tx for testing purposes
rx = StringIO()  # Mock receive channel
tx = StringIO()  # Mock transmit channel

server = CopilotLanguageServer(rx, tx)