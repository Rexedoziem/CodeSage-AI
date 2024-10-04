"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TelemetryService = void 0;
const vscode = require("vscode");
const extension_telemetry_1 = require("@vscode/extension-telemetry");
class TelemetryService {
    constructor() {
        // Create TelemetryReporter with extension ID and version
        const extensionId = 'advanced-python-copilot';
        const extensionVersion = vscode.extensions.getExtension(extensionId)?.packageJSON.version || '0.0.0';
        this.reporter = new extension_telemetry_1.default(extensionId, extensionVersion);
    }
    trackEvent(eventName, properties, measurements) {
        this.reporter.sendTelemetryEvent(eventName, properties, measurements);
    }
    dispose() {
        this.reporter.dispose();
    }
}
exports.TelemetryService = TelemetryService;
//# sourceMappingURL=telemetryService.js.map