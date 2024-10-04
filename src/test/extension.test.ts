import * as assert from 'assert';
import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

suite('LanguageClient Tests', () => {
    test('LanguageClient constructor should create a new instance', () => {
        const client = new LanguageClient(
            'testClientId',
            'Test Language Client',
            {
                run: { module: 'path/to/server/module' },
                debug: { module: 'path/to/server/module' }
            },
            {}
        );
        assert.ok(client instanceof LanguageClient);
    });

    test('LanguageClient should throw error with invalid server options', () => {
        assert.throws(() => {
            new LanguageClient(
                'testClientId',
                'Test Language Client',
                {} as any,
                {}
            );
        }, Error);
    });

    test('LanguageClient should accept valid client options', () => {
        const client = new LanguageClient(
            'testClientId',
            'Test Language Client',
            {
                run: { module: 'path/to/server/module' },
                debug: { module: 'path/to/server/module' }
            },
            {
                documentSelector: [{ scheme: 'file', language: 'typescript' }],
                synchronize: {
                    fileEvents: vscode.workspace.createFileSystemWatcher('**/*.ts')
                }
            }
        );
        assert.ok(client instanceof LanguageClient);
    });
});
