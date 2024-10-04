import { LanguageClient } from 'vscode-languageclient/node';

export class FeedbackManager {
    constructor(private client: LanguageClient) {}

    async recordCompletion(completion: string) {
        await this.client.sendNotification('recordCompletion', { completion });
    }

    async provideFeedback(completion: string, rating: number) {
        await this.client.sendNotification('provideFeedback', { completion, rating });
    }
}