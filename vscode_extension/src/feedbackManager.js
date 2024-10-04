"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FeedbackManager = void 0;
class FeedbackManager {
    constructor(client) {
        this.client = client;
    }
    async recordCompletion(completion) {
        await this.client.sendNotification('recordCompletion', { completion });
    }
    async provideFeedback(completion, rating) {
        await this.client.sendNotification('provideFeedback', { completion, rating });
    }
}
exports.FeedbackManager = FeedbackManager;
//# sourceMappingURL=feedbackManager.js.map