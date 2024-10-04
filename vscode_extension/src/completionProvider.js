"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CompletionProvider = void 0;
const vscode = require("vscode");
const axios_1 = require("axios");
const telemetryService_1 = require("./telemetryService");
class CompletionProvider {
    constructor() {
        this.telemetryService = new telemetryService_1.TelemetryService();
    }
    async provideCompletionItems(document, position, token, context) {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);
        if (!linePrefix.endsWith('.')) {
            return [];
        }
        try {
            const response = await axios_1.default.post('http://localhost:8080/complete', {
                code_context: document.getText(),
                user_id: await this.getUserId() // In a real scenario, you'd get this from user authentication
            });
            this.telemetryService.trackEvent('completion', { status: response.status.toString() });
            return response.data.map((suggestion) => {
                const item = new vscode.CompletionItem(suggestion);
                item.kind = vscode.CompletionItemKind.Snippet;
                item.insertText = suggestion;
                return item;
            });
        }
        catch (error) {
            console.error('Error fetching completions:', error);
            if (error instanceof Error) {
                this.telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: error.message });
            }
            else {
                this.telemetryService.trackEvent('error', { type: 'completion_fetch_error', message: 'Unknown error' });
            }
            return [];
        }
    }
    async getUserId() {
        const session = await vscode.authentication.getSession('your-auth-provider-id', ['user-read']);
        return session ? session.id : 'anonymous';
    }
}
exports.CompletionProvider = CompletionProvider;
//# sourceMappingURL=completionProvider.js.map