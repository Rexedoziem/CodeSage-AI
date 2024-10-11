import * as vscode from 'vscode';
import { LanguageClient, TransportKind } from 'vscode-languageclient/node';
import { debounce } from 'lodash';
//import axios from 'axios';

// Import custom classes
import { FeedbackManager } from './feedbackManager';
import { SecureStorage } from './secureStorage';
import { TelemetryService } from './telemetryService';

let client: LanguageClient;
let feedbackManager: FeedbackManager;
let secureStorage: SecureStorage;
let telemetryService: TelemetryService;

export function activate(context: vscode.ExtensionContext) {
    // Initialize services
    secureStorage = new SecureStorage(context);
    telemetryService = new TelemetryService();

    // Initialize the language client
    client = new LanguageClient(
        'advancedPythonCopilot',
        'Advanced Python Copilot',
        {
            run: { module: 'C:/Users/HP/Desktop/CO_PILOT/advanced_copilot/language_server/server.py', transport: TransportKind.ipc },
            debug: { module: 'C:/Users/HP/Desktop/CO_PILOT/advanced_copilot/language_server/server.py', transport: TransportKind.ipc, options: { execArgv: ['--nolazy', '--inspect=6009'] } }
        },
        {
            documentSelector: [{ scheme: 'file', language: '*' }],
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc')
            }
        }
    );

    client.start();

    // Initialize FeedbackManager
    feedbackManager = new FeedbackManager(client);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('advancedPythonCopilot.signIn', signIn),
        vscode.commands.registerCommand('advancedPythonCopilot.signOut', signOut),
        vscode.commands.registerCommand('advancedPythonCopilot.getCompletion', debounce(getCompletion, 300)),
        vscode.commands.registerCommand('advancedPythonCopilot.getCompletionAndFixes', debounce(getCompletionAndFixes, 300))
    );

    // Register completion provider
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        { pattern: '**' },
        new CompletionProvider(),
        '.' // Trigger completion after a dot
    );

    context.subscriptions.push(completionProvider);

    // Check for existing authentication
    checkAuthentication();

    // Listen for authentication status notifications from the server
    client.onNotification('copilot/authenticationStatus', handleAuthStatusNotification);
}

class CompletionProvider implements vscode.CompletionItemProvider {
    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);
        if (!linePrefix.endsWith('.')) {
            return [];
        }

        try {
            const response: any[] = await client.sendRequest('completions', {
                textDocument: { uri: document.uri.toString() },
                position: { line: position.line, character: position.character }
            });

            telemetryService.trackEvent('completion', { status: 'success' });

            return response.map((item: any) => {
                const completionItem = new vscode.CompletionItem(item.label);
                completionItem.kind = vscode.CompletionItemKind.Snippet;
                completionItem.insertText = item.insertText;
                completionItem.detail = item.detail;
                return completionItem;
            });
        } catch (error: unknown) {
            console.error('Error fetching completions:', error);
            if (error instanceof Error) {
                telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: error.message });
            } else {
                telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: 'Unknown error' });
            }
            return [];
        }
    }}

async function signIn() {
    const result = await vscode.authentication.getSession('github', ['read:user'], { createIfNone: true });
    if (result) {
        const token = result.accessToken;
        await client.sendRequest('copilot.authenticate', { token });
    } else {
        vscode.window.showErrorMessage('Failed to authenticate with GitHub.');
    }
}

async function signOut() {
    await client.sendRequest('copilot.signOut');
    await secureStorage.deleteSecret('userToken');
    vscode.window.showInformationMessage('Signed out successfully.');
}

async function checkAuthentication() {
    const storedToken = await secureStorage.getSecret('userToken');
    if (storedToken) {
        await client.sendRequest('copilot.authenticate', { token: storedToken });
    } else {
        showSignInPrompt();
    }
}

function showSignInPrompt() {
    vscode.window.showInformationMessage(
        'Sign in to use Advanced Python Copilot',
        'Sign In'
    ).then(selection => {
        if (selection === 'Sign In') {
            vscode.commands.executeCommand('advancedPythonCopilot.signIn');
        }
    });
}

function handleAuthStatusNotification(params: { success: boolean, message: string }) {
    if (params.success) {
        vscode.window.showInformationMessage(params.message);
    } else {
        vscode.window.showErrorMessage(params.message);
        showSignInPrompt();
    }
}

async function getCompletion() {
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const position = editor.selection.active;
        const document = editor.document;

        try {
            const completions = await client.sendRequest('completions', {
                textDocument: { uri: document.uri.toString() },
                position: { line: position.line, character: position.character }
            }) as Array<{ label: string; detail: string }>;

            const quickPick = vscode.window.createQuickPick();
            quickPick.items = completions.map((item) => ({
                label: item.label,
                detail: item.detail
            }));

            quickPick.onDidChangeSelection(selection => {
                if (selection[0]) {
                    editor.edit(editBuilder => {
                        editBuilder.insert(position, selection[0].label);
                    });
                    quickPick.hide();
                    feedbackManager.recordCompletion(selection[0].label);
                }
            });

            quickPick.onDidHide(() => quickPick.dispose());
            quickPick.show();
        } catch (error) {
            vscode.window.showErrorMessage('Failed to get completions. Please check your authentication status.');
        }
    }
}
async function getCompletionAndFixes() {
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const document = editor.document;
        const codeContext = document.getText();

        const completionsAndFixes = await client.sendRequest('getCompletionsAndFixes', { codeContext }) as Array<[string, string]>;
        
        const quickPick = vscode.window.createQuickPick();
        quickPick.items = completionsAndFixes.map(([text, type]) => ({
            label: type === 'error_fix' ? `🔧 ${text}` : `💡 ${text}`,
            detail: type === 'error_fix' ? 'Error Fix' : 'Completion'
        }));
        
        quickPick.onDidChangeSelection(selection => {
            if (selection[0]) {
                if (selection[0].detail === 'Error Fix') {
                    vscode.window.showInformationMessage(selection[0].label);
                } else {
                    editor.edit(editBuilder => {
                        editBuilder.insert(editor.selection.active, selection[0].label.slice(2));
                    });
                }
                quickPick.hide();
            }
        });
        
        quickPick.onDidHide(() => quickPick.dispose());
        quickPick.show();
    }
}

export function deactivate() {
    if (client) {
        client.stop();
    }
    telemetryService.dispose();
}