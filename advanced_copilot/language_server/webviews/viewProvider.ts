import * as vscode from 'vscode';

export function activateSignInWebview(context: vscode.ExtensionContext) {
    const panel = vscode.window.createWebviewPanel(
        'copilotSignIn',
        'Your Copilot Sign In',
        vscode.ViewColumn.One,
        {}
    );

    panel.webview.html = getWebviewContent();

    // Handle messages from the webview
    panel.webview.onDidReceiveMessage(
        message => {
            switch (message.command) {
                case 'signIn':
                    // Implement sign in logic
                    break;
                case 'register':
                    // Implement registration logic
                    break;
            }
        },
        undefined,
        context.subscriptions
    );
}

function getWebviewContent() {
    return `<!DOCTYPE html>
    <html lang="en">
    <body>
        <h1>Welcome to Your Copilot</h1>
        <button onclick="signIn()">Sign in to use Your Copilot</button>
        <button onclick="register()">Register for Your Copilot</button>
        <a href="#">Learn more about Your Copilot</a>
        <script>
            const vscode = acquireVsCodeApi();
            function signIn() {
                vscode.postMessage({ command: 'signIn' });
            }
            function register() {
                vscode.postMessage({ command: 'register' });
            }
        </script>
    </body>
    </html>`;
}