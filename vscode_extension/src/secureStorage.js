"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SecureStorage = void 0;
class SecureStorage {
    constructor(secrets) {
        this.secrets = secrets;
    }
    async storeSecret(key, value) {
        await this.secrets.store(key, value);
    }
    async getSecret(key) {
        return await this.secrets.get(key);
    }
    async deleteSecret(key) {
        await this.secrets.delete(key);
    }
}
exports.SecureStorage = SecureStorage;
//# sourceMappingURL=secureStorage.js.map