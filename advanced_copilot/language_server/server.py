import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import configparser
from pylsp import uris
from pylsp.workspace import Document
from pylsp.python_lsp import PythonLSPServer
from security.auth import AuthManager
from security.user_store import UserStore
from completion_provider import CompletionProvider

# Default configuration
DEFAULT_CONFIG = {
    'DatabasePath': 'user_data.db',
    'SecretKey': 'default_secret_key',
    'ModelPath': 'Rexe/llama-3.1-codegen-merged',
    'Device': 'cpu'
}

config = configparser.ConfigParser()
config['DEFAULT'] = DEFAULT_CONFIG

class CopilotLanguageServer(PythonLSPServer):
    def __init__(self, rx, tx):
        super().__init__(rx, tx)
        self.user_store = UserStore(config['DEFAULT']['DatabasePath'])
        self.auth_manager = AuthManager(secret_key=config['DEFAULT']['SecretKey'], user_store=self.user_store)
        self.completion_provider: Optional[CompletionProvider] = None
        self.current_user: Optional[str] = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.logger.info("Starting CopilotLanguageServer")
        try:
            await super().start()
            # Register handlers
            self._jsonrpc_methods.update({
                'textDocument/didChange': self.text_document_did_change,
                'textDocument/completion': self.completions,
                'workspace/executeCommand': self.execute_command,
            })
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Server received cancellation request")
        except Exception as e:
            self.logger.error(f"Error in server: {str(e)}")
            raise
        finally:
            self.logger.info("Server shutting down")

    async def __aenter__(self):
        self.logger.info("Entering CopilotLanguageServer context")
        # Initialize any resources that need async setup
        self.completion_provider = CompletionProvider(
            config['DEFAULT']['ModelPath'], 
            device=config['DEFAULT']['Device'],
            token='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'
        )
        await self.completion_provider  # Assuming there's an async initialize method
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.logger.info("Exiting CopilotLanguageServer context")
        # Cleanup resources
        if self.completion_provider:
            await self.completion_provider.close()
        if self.user_store:
            await self.user_store.close()  # Assuming there's an async close method
        if exc_type:
            self.logger.error(f"An error occurred: {exc_type.__name__}: {exc_val}")
        return False  # Propagate exceptions

    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await super().initialize(params)
        self.logger.info("Copilot Language Server initializing")
        return result

    async def initialized(self):
        await super().initialized()
        self.logger.info("Copilot Language Server initialized")

    async def authenticate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            token = params.get('token')
            if not token:
                return {"success": False, "message": "No token provided"}
            username = self.auth_manager.verify_token(token)
            if not username:
                return {"success": False, "message": "Invalid token"}
            await self.initialize_user_session(username)
            return {"success": True, "message": f"Authenticated as {username}"}
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return {"success": False, "message": "Authentication failed"}

    async def initialize_user_session(self, username: str):
        if not self.completion_provider:
            self.completion_provider = CompletionProvider(
                config['DEFAULT']['ModelPath'], 
                device=config['DEFAULT']['Device'],
                token='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'
            )
            #await self.completion_provider.initialize()  # Assuming there's an async initialize method
        self.current_user = username
        self.logger.info(f"User session initialized for {username}")

    async def completions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.completion_provider or not self.current_user:
            self.logger.warning("Completion requested but user is not authenticated or CompletionProvider not initialized")
            return []

        uri = params['textDocument']['uri']
        position = params['position']
        document = self.workspace.get_document(uri)
        code_context = self.get_code_context(document, position)

        completions = []
        try:
            async for completion, language in self.completion_provider.get_completions(
                user_id=self.current_user,
                code_context=code_context
            ):
                completions.append({
                    'label': completion,
                    'kind': 15,  # Snippet
                    'detail': f'Copilot suggestion ({language})',
                    'insertText': completion
                })
        except Exception as e:
            self.logger.error(f"Error getting completions: {str(e)}")

        return completions

    def get_code_context(self, document: Document, position: Dict[str, int]) -> str:
        lines = document.lines[:position['line'] + 1]
        lines[-1] = lines[-1][:position['character']]
        return '\n'.join(lines)

    def capabilities(self) -> Dict[str, Any]:
        capabilities = super().capabilities()
        capabilities.update({
            'textDocumentSync': {
                'change': 2,  # Incremental
                'save': {
                    'includeText': False
                },
                'openClose': True,
            },
            'completionProvider': {
                'triggerCharacters': ['.', ' ']  # Trigger on space for in-line completions
            },
            'executeCommandProvider': {
                'commands': ['copilot.authenticate', 'copilot.signOut']
            }
        })
        return capabilities

    async def execute_command(self, params: Dict[str, Any]) -> None:
        command = params['command']
        if command == 'copilot.authenticate':
            result = await self.authenticate(params.get('arguments', [{}])[0])
            await self.send_notification("copilot/authenticationStatus", result)
        elif command == 'copilot.signOut':
            self.current_user = None
            self.completion_provider = None
            await self.send_notification("copilot/authenticationStatus", {"success": True, "message": "Signed out successfully"})

    async def text_document_did_change(self, params: Dict[str, Any]):
        await super().text_document_did_change(params)
        # Trigger completion after each change
        uri = params['textDocument']['uri']
        position = params['contentChanges'][-1]['range']['end']
        completions = await self.completions({
            'textDocument': {'uri': uri},
            'position': position
        })
        if completions:
            await self.send_notification("textDocument/completion", {'items': completions})

    async def send_notification(self, method: str, params: Dict[str, Any]):
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        await self.write_notification(notification)

    async def write_notification(self, notification: Dict[str, Any]):
        await self.transport.write(json.dumps(notification).encode() + b'\r\n')

async def run_server():
    logger = logging.getLogger(__name__)
    logger.info("Initializing server")
    try:
        reader = asyncio.StreamReader()
        loop = asyncio.get_running_loop()
        transport = asyncio.WriteTransport()
        protocol = asyncio.StreamReaderProtocol(reader)
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        
        async with CopilotLanguageServer(reader, writer) as server:
            logger.info("Server initialized, starting main loop")
            await server.start()
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        logger.info("Server shutting down")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting main function")
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}", exc_info=True)
    finally:
        logger.info("Main function completed")