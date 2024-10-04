// secureStorage.ts
import * as vscode from 'vscode';

export class SecureStorage {
    private storage: vscode.SecretStorage;

    constructor(context: vscode.ExtensionContext) {
        this.storage = context.secrets;
    }

    public async storeSecret(key: string, value: string) {
        await this.storage.store(key, value);
    }

    public async getSecret(key: string): Promise<string | undefined> {
        return await this.storage.get(key);
    }
}