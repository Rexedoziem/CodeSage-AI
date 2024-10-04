import * as vscode from 'vscode';
import TelemetryReporter from '@vscode/extension-telemetry';

export class TelemetryService {
    private reporter: TelemetryReporter;
    constructor() {
        // Create TelemetryReporter with extension ID and version
        const extensionId = 'advanced-python-copilot';
        const extensionVersion = vscode.extensions.getExtension(extensionId)?.packageJSON.version || '0.0.0';
        this.reporter = new TelemetryReporter(extensionId, extensionVersion);
    }

    trackEvent(eventName: string, properties?: { [key: string]: string }, measurements?: { [key: string]: number }) {
        this.reporter.sendTelemetryEvent(eventName, properties, measurements);
    }

    dispose() {
        this.reporter.dispose();
    }
}