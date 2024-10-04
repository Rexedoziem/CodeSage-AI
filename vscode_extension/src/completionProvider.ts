import * as vscode from 'vscode';
import axios from 'axios';
import { TelemetryService } from './telemetryService';

export class CompletionProvider implements vscode.CompletionItemProvider {
    private telemetryService: TelemetryService;

    constructor() {
        this.telemetryService = new TelemetryService();
    }

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
                user_id: await this.getUserId() // In a real scenario, you'd get this from user authentication
            });

            this.telemetryService.trackEvent('completion', { status: response.status.toString() });

            return response.data.map((suggestion: string) => {
                const item = new vscode.CompletionItem(suggestion);
                item.kind = vscode.CompletionItemKind.Snippet;
                item.insertText = suggestion;
                return item;
            });
        } catch (error: unknown) {
            console.error('Error fetching completions:', error);
            if (error instanceof Error) {
                this.telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: error.message });
            } else {
                this.telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: 'Unknown error' });
            }

            return [];
        }
    }    private async getUserId(): Promise<string> {
        const session = await vscode.authentication.getSession('your-auth-provider-id', ['user-read']);
        return session ? session.id : 'anonymous';
    }
}