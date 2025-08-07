export declare abstract class MCPError extends Error {
    readonly code: number;
    readonly timestamp: Date;
    readonly correlationId: string | undefined;
    readonly context: Record<string, unknown> | undefined;
    readonly recoverable: boolean;
    constructor(message: string, code: number, recoverable?: boolean, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        code: number;
        message: string;
        data?: Record<string, unknown>;
    };
    toLogFormat(): {
        name: string;
        message: string;
        code: number;
        timestamp: string;
        correlationId: string | undefined;
        context: Record<string, unknown> | undefined;
        recoverable: boolean;
        stack: string | undefined;
    };
}
export declare class ProtocolError extends MCPError {
    constructor(message: string, code?: number, correlationId?: string, context?: Record<string, unknown>);
}
export declare class ValidationError extends MCPError {
    readonly field: string | undefined;
    readonly value: unknown | undefined;
    constructor(message: string, field?: string, value?: unknown, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            field: string | undefined;
            value: unknown;
        };
        code: number;
        message: string;
    };
}
export declare class ToolError extends MCPError {
    readonly toolName: string;
    readonly operation: string;
    constructor(message: string, toolName: string, operation?: string, recoverable?: boolean, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            toolName: string;
            operation: string;
        };
        code: number;
        message: string;
    };
}
export declare class NotFoundError extends MCPError {
    readonly resourceType: string;
    readonly resourceId: string;
    constructor(resourceType: string, resourceId: string, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            resourceType: string;
            resourceId: string;
        };
        code: number;
        message: string;
    };
}
export declare class RateLimitError extends MCPError {
    readonly limit: number;
    readonly windowMs: number;
    readonly resetTime: Date;
    constructor(limit: number, windowMs: number, resetTime: Date, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            limit: number;
            windowMs: number;
            resetTime: string;
            retryAfter: number;
        };
        code: number;
        message: string;
    };
}
export declare class AuthenticationError extends MCPError {
    readonly authType: string;
    constructor(message: string, authType?: string, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            authType: string;
        };
        code: number;
        message: string;
    };
}
export declare class TimeoutError extends MCPError {
    readonly operation: string;
    readonly timeoutMs: number;
    constructor(operation: string, timeoutMs: number, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            operation: string;
            timeoutMs: number;
        };
        code: number;
        message: string;
    };
}
export declare class ConfigurationError extends MCPError {
    readonly configKey: string;
    readonly expectedType: string | undefined;
    constructor(message: string, configKey: string, expectedType?: string, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            configKey: string;
            expectedType: string | undefined;
        };
        code: number;
        message: string;
    };
}
export declare class ResourceLimitError extends MCPError {
    readonly resource: string;
    readonly limit: number;
    readonly current: number;
    constructor(resource: string, limit: number, current: number, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            resource: string;
            limit: number;
            current: number;
        };
        code: number;
        message: string;
    };
}
export declare class InternalServerError extends MCPError {
    constructor(message: string, correlationId?: string, context?: Record<string, unknown>);
}
export declare class DependencyError extends MCPError {
    readonly dependency: string;
    constructor(dependency: string, message?: string, correlationId?: string, context?: Record<string, unknown>);
    toJSONRPC(): {
        data: {
            dependency: string;
        };
        code: number;
        message: string;
    };
}
export declare class MCPErrorFactory {
    static fromError(error: Error, correlationId?: string, context?: Record<string, unknown>): MCPError;
    static validation(field: string, value: unknown, expectedType?: string, correlationId?: string): ValidationError;
    static toolError(toolName: string, operation: string, message: string, recoverable?: boolean, correlationId?: string): ToolError;
    static notFound(resourceType: string, resourceId: string, correlationId?: string): NotFoundError;
    static rateLimit(limit: number, windowMs: number, resetTime: Date, correlationId?: string): RateLimitError;
    static timeout(operation: string, timeoutMs: number, correlationId?: string): TimeoutError;
    static config(configKey: string, message: string, expectedType?: string, correlationId?: string): ConfigurationError;
    static resourceLimit(resource: string, limit: number, current: number, correlationId?: string): ResourceLimitError;
    static dependency(dependency: string, message?: string, correlationId?: string): DependencyError;
}
export declare const ErrorCodes: {
    readonly PARSE_ERROR: -32700;
    readonly INVALID_REQUEST: -32600;
    readonly METHOD_NOT_FOUND: -32601;
    readonly INVALID_PARAMS: -32602;
    readonly INTERNAL_ERROR: -32603;
    readonly SERVER_ERROR_BASE: -32000;
    readonly RATE_LIMIT_EXCEEDED: -32000;
    readonly TOOL_ERROR: -32001;
    readonly TIMEOUT_ERROR: -32002;
    readonly CONFIGURATION_ERROR: -32003;
    readonly RESOURCE_LIMIT_ERROR: -32004;
    readonly AUTH_ERROR: -32005;
    readonly DEPENDENCY_ERROR: -32006;
};
export declare function isMCPError(error: unknown): error is MCPError;
export declare function isRecoverableError(error: unknown): boolean;
//# sourceMappingURL=MCPErrors.d.ts.map