"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const node_1 = require("vscode-languageclient/node");
const lodash_1 = require("lodash");
let client;
let token = null;
function activate(context) {
    // Initialize the language client
    client = new node_1.LanguageClient('advancedPythonCopilot', 'Advanced Python Copilot', {
        run: { module: 'C:/Users/HP/Desktop/CO_PILOT/advanced_copilot/language_server/server.py', transport: node_1.TransportKind.ipc },
        debug: { module: 'C:/Users/HP/Desktop/CO_PILOT/advanced_copilot/language_server/server.py', transport: node_1.TransportKind.ipc, options: { execArgv: ['--nolazy', '--inspect=6009'] } }
    }, {
        documentSelector: [{ scheme: 'file', language: '*' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc')
        }
    });
    client.start();
    // Register commands
    context.subscriptions.push(vscode.commands.registerCommand('advancedPythonCopilot.register', registerUser), vscode.commands.registerCommand('advancedPythonCopilot.login', loginUser), vscode.commands.registerCommand('advancedPythonCopilot.getCompletion', getCompletion), vscode.commands.registerCommand('advancedPythonCopilot.getCompletionAndFixes', getCompletionAndFixes));
    // Register inline completion provider
    const inlineProvider = vscode.languages.registerInlineCompletionItemProvider({ pattern: '**' }, {
        provideInlineCompletionItems: (0, lodash_1.debounce)(provideInlineCompletionItems, 300)
    });
    context.subscriptions.push(inlineProvider);
}
exports.activate = activate;
async function registerUser() {
    const username = await vscode.window.showInputBox({ prompt: 'Enter username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });
    if (username && password) {
        const result = await client.sendRequest('register', { username, password });
        if (result) {
            vscode.window.showInformationMessage('Registration successful. Please log in.');
        }
        else {
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
            vscode.window.showInformationMessage('Login successful.');
        }
        else {
            vscode.window.showErrorMessage('Login failed. Please check your credentials.');
        }
    }
}
async function getCompletion() {
    if (!token) {
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
        });
        const quickPick = vscode.window.createQuickPick();
        quickPick.items = [];
        quickPick.onDidChangeSelection(selection => {
            if (selection[0]) {
                editor.edit(editBuilder => {
                    editBuilder.insert(position, selection[0].label);
                });
                quickPick.hide();
            }
        });
        quickPick.onDidHide(() => quickPick.dispose());
        quickPick.show();
        for await (const { completion, language, issues } of completionStream) {
            const issueCount = Object.values(issues).flat().length;
            const issueWarning = issueCount > 0 ? `(${issueCount} issues) ` : '';
            quickPick.items = [...quickPick.items, {
                    label: `${issueWarning}${completion}`,
                    description: `Language: ${language}`
                }];
            // Show issues in Problems panel
            const diagnostics = issues.errors.concat(issues.warnings, issues.style_issues, issues.security_issues)
                .map((issue) => new vscode.Diagnostic(new vscode.Range(issue.line - 1, issue.column - 1, issue.line - 1, issue.column), issue.message, issue.message.startsWith("Error") ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning));
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
        const completionsAndFixes = await client.sendRequest('getCompletionsAndFixes', { codeContext });
        const quickPick = vscode.window.createQuickPick();
        quickPick.items = completionsAndFixes.map(([text, type]) => ({
            label: type === 'error_fix' ? `🔧 ${text}` : `💡 ${text}`,
            detail: type === 'error_fix' ? 'Error Fix' : 'Completion'
        }));
        quickPick.onDidChangeSelection(selection => {
            if (selection[0]) {
                if (selection[0].detail === 'Error Fix') {
                    vscode.window.showInformationMessage(selection[0].label);
                }
                else {
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
async function provideInlineCompletionItems(document, position, context, token) {
    const codeContext = document.getText(new vscode.Range(new vscode.Position(0, 0), position));
    const completions = await client.sendRequest('getInlineCompletions', { codeContext });
    return completions.map(completion => ({
        insertText: completion,
        range: new vscode.Range(position, position)
    }));
}
function deactivate() {
    if (client) {
        return client.stop();
    }
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map