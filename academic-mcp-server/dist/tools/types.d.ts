import { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
export interface ToolParameterSchema {
    type: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'null';
    properties?: Record<string, ToolParameterSchema>;
    items?: ToolParameterSchema;
    required?: string[];
    description?: string;
    enum?: unknown[];
    minimum?: number;
    maximum?: number;
    minLength?: number;
    maxLength?: number;
    pattern?: string;
}
export interface ToolMetadata {
    name: string;
    description: string;
    version: string;
    inputSchema: ToolParameterSchema;
    category?: string;
    tags?: string[];
    deprecated?: boolean;
    experimental?: boolean;
}
export interface ToolContext {
    requestId: string;
    userId?: string;
    sessionId?: string;
    timestamp: Date;
    metadata: Record<string, unknown>;
}
export type ToolHandler = (args: Record<string, unknown>, context: ToolContext) => Promise<CallToolResult>;
export interface ToolRegistration {
    metadata: ToolMetadata;
    handler: ToolHandler;
    permissions?: string[];
    rateLimit?: {
        requests: number;
        windowMs: number;
    };
}
export interface ToolValidationResult {
    valid: boolean;
    errors: string[];
    warnings?: string[] | undefined;
}
export interface ToolRegistryEvents {
    'tool-registered': (name: string, metadata: ToolMetadata) => void;
    'tool-unregistered': (name: string) => void;
    'tool-called': (name: string, context: ToolContext) => void;
    'tool-error': (name: string, error: Error, context: ToolContext) => void;
    'validation-failed': (name: string, errors: string[]) => void;
}
export interface ToolRegistryConfig {
    enableValidation: boolean;
    enablePermissions: boolean;
    enableRateLimit: boolean;
    maxTools: number;
    defaultCategory: string;
}
//# sourceMappingURL=types.d.ts.map