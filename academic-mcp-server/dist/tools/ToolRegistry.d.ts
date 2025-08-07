import { EventEmitter } from 'events';
import { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { ToolRegistration, ToolMetadata, ToolContext, ToolValidationResult, ToolRegistryConfig, ToolRegistryEvents } from './types';
export declare class ToolRegistry extends EventEmitter {
    private tools;
    private config;
    private callCounts;
    constructor(config?: Partial<ToolRegistryConfig>);
    registerTool(registration: ToolRegistration): Promise<void>;
    unregisterTool(name: string): Promise<boolean>;
    getToolMetadata(name: string): ToolMetadata | null;
    getAllToolsMetadata(): ToolMetadata[];
    getToolsByCategory(category: string): ToolMetadata[];
    getToolsByTag(tag: string): ToolMetadata[];
    searchTools(query: string): ToolMetadata[];
    hasTools(name: string): boolean;
    getToolCount(): number;
    getStats(): {
        totalTools: number;
        categoryCounts: Record<string, number>;
        deprecatedTools: string[];
        experimentalTools: string[];
    };
    executeTool(name: string, args: Record<string, unknown>, context: ToolContext): Promise<CallToolResult>;
    private checkRateLimit;
    clear(): void;
    validateAllTools(): Record<string, ToolValidationResult>;
    getConfig(): Readonly<ToolRegistryConfig>;
    updateConfig(newConfig: Partial<ToolRegistryConfig>): void;
    emit<K extends keyof ToolRegistryEvents>(event: K, ...args: Parameters<ToolRegistryEvents[K]>): boolean;
    on<K extends keyof ToolRegistryEvents>(event: K, listener: ToolRegistryEvents[K]): this;
    off<K extends keyof ToolRegistryEvents>(event: K, listener: ToolRegistryEvents[K]): this;
}
//# sourceMappingURL=ToolRegistry.d.ts.map