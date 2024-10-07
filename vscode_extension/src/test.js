import * as vscode from 'vscode';
import { LanguageClient, TransportKind } from 'vscode-languageclient/node';
import { debounce } from 'lodash';
import axios from 'axios';

// Import custom classes
import { FeedbackManager } from './feedbackManager';
import { SecureStorage } from './secureStorage';
import { TelemetryService } from './telemetryService';

let client: LanguageClient;
let token: string | null = null;
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
        vscode.commands.registerCommand('advancedPythonCopilot.register', registerUser),
        vscode.commands.registerCommand('advancedPythonCopilot.login', loginUser),
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
            const response = await axios.post('http://localhost:8080/complete', {
                code_context: document.getText(),
                user_id: await this.getUserId()
            });

            telemetryService.trackEvent('completion', { status: response.status.toString() });

            return response.data.map((suggestion: string) => {
                const item = new vscode.CompletionItem(suggestion);
                item.kind = vscode.CompletionItemKind.Snippet;
                item.insertText = suggestion;
                return item;
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
    }

    private async getUserId(): Promise<string> {
        const session = await vscode.authentication.getSession('your-auth-provider-id', ['user-read']);
        return session ? session.id : 'anonymous';
    }
}

async function registerUser() {
    const username = await vscode.window.showInputBox({ prompt: 'Enter username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });
    if (username && password) {
        const result = await client.sendRequest('register', { username, password });
        if (result) {
            vscode.window.showInformationMessage('Registration successful. Please log in.');
        } else {
            vscode.window.showErrorMessage('Registration failed. Username may already exist.');
        }
    }
}

async function loginUser() {
    const username = await vscode.window.showInputBox({ prompt: 'Enter username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });
    if (username && password) {
        token = await client.sendRequest('login', { username, password });
        if (token) {
            await secureStorage.storeSecret('userToken', token);
            vscode.window.showInformationMessage('Login successful.');
        } else {
            vscode.window.showErrorMessage('Login failed. Please check your credentials.');
        }
    }
}

async function getCompletion() {
    const storedToken = await secureStorage.getSecret('userToken');
    if (!storedToken) {
        vscode.window.showErrorMessage('Please log in to use the copilot.');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const position = editor.selection.active;
        const document = editor.document;
        const codeContext = document.getText(new vscode.Range(new vscode.Position(0, 0), position));

        const completionStream = await client.sendRequest('getCompletionsStream', { 
            codeContext, 
            filePath: document.fileName 
        }) as AsyncIterable<{ completion: string; language: string; issues: { errors: any[]; warnings: any[]; style_issues: any[]; security_issues: any[] } }>;
        
        const quickPick = vscode.window.createQuickPick();
        quickPick.items = [];
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

        for await (const { completion, language, issues } of completionStream) {
            const issueCount = Object.values(issues).reduce((acc, val) => acc + val.length, 0);
            const issueWarning = issueCount > 0 ? `(${issueCount} issues) ` : '';
            quickPick.items = [...quickPick.items, { 
                label: `${issueWarning}${completion}`,
                description: `Language: ${language}`
            }];

            // Show issues in Problems panel
            const diagnostics = issues.errors.concat(issues.warnings, issues.style_issues, issues.security_issues)
                .map((issue: { line: number; column: number; message: string }) => new vscode.Diagnostic(
                    new vscode.Range(issue.line - 1, issue.column - 1, issue.line - 1, issue.column),
                    issue.message,
                    issue.message.startsWith("Error") ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning
                ));
            
            vscode.languages.createDiagnosticCollection('advancedPythonCopilot')
                .set(document.uri, diagnostics);
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