"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorCodes = exports.MCPErrorFactory = exports.DependencyError = exports.InternalServerError = exports.ResourceLimitError = exports.ConfigurationError = exports.TimeoutError = exports.AuthenticationError = exports.RateLimitError = exports.NotFoundError = exports.ToolError = exports.ValidationError = exports.ProtocolError = exports.MCPError = void 0;
exports.isMCPError = isMCPError;
exports.isRecoverableError = isRecoverableError;
class MCPError extends Error {
    constructor(message, code, recoverable = false, correlationId, context) {
        super(message);
        this.name = this.constructor.name;
        this.code = code;
        this.timestamp = new Date();
        this.correlationId = correlationId;
        this.context = context;
        this.recoverable = recoverable;
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
    }
    toJSONRPC() {
        return {
            code: this.code,
            message: this.message,
            data: {
                timestamp: this.timestamp.toISOString(),
                correlationId: this.correlationId,
                context: this.context,
                recoverable: this.recoverable,
                stack: this.stack,
            },
        };
    }
    toLogFormat() {
        return {
            name: this.name,
            message: this.message,
            code: this.code,
            timestamp: this.timestamp.toISOString(),
            correlationId: this.correlationId,
            context: this.context,
            recoverable: this.recoverable,
            stack: this.stack,
        };
    }
}
exports.MCPError = MCPError;
class ProtocolError extends MCPError {
    constructor(message, code = -32603, correlationId, context) {
        super(message, code, false, correlationId, context);
    }
}
exports.ProtocolError = ProtocolError;
class ValidationError extends MCPError {
    constructor(message, field, value, correlationId, context) {
        super(message, -32602, false, correlationId, context);
        this.field = field;
        this.value = value;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                field: this.field,
                value: this.value,
            },
        };
    }
}
exports.ValidationError = ValidationError;
class ToolError extends MCPError {
    constructor(message, toolName, operation = 'execute', recoverable = true, correlationId, context) {
        super(message, -32001, recoverable, correlationId, context);
        this.toolName = toolName;
        this.operation = operation;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                toolName: this.toolName,
                operation: this.operation,
            },
        };
    }
}
exports.ToolError = ToolError;
class NotFoundError extends MCPError {
    constructor(resourceType, resourceId, correlationId, context) {
        const message = `${resourceType} '${resourceId}' not found`;
        super(message, -32601, false, correlationId, context);
        this.resourceType = resourceType;
        this.resourceId = resourceId;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                resourceType: this.resourceType,
                resourceId: this.resourceId,
            },
        };
    }
}
exports.NotFoundError = NotFoundError;
class RateLimitError extends MCPError {
    constructor(limit, windowMs, resetTime, correlationId, context) {
        const message = `Rate limit exceeded: ${limit} requests per ${windowMs}ms window`;
        super(message, -32000, true, correlationId, context);
        this.limit = limit;
        this.windowMs = windowMs;
        this.resetTime = resetTime;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                limit: this.limit,
                windowMs: this.windowMs,
                resetTime: this.resetTime.toISOString(),
                retryAfter: Math.ceil((this.resetTime.getTime() - Date.now()) / 1000),
            },
        };
    }
}
exports.RateLimitError = RateLimitError;
class AuthenticationError extends MCPError {
    constructor(message, authType = 'unknown', correlationId, context) {
        super(message, -32005, false, correlationId, context);
        this.authType = authType;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                authType: this.authType,
            },
        };
    }
}
exports.AuthenticationError = AuthenticationError;
class TimeoutError extends MCPError {
    constructor(operation, timeoutMs, correlationId, context) {
        const message = `Operation '${operation}' timed out after ${timeoutMs}ms`;
        super(message, -32002, true, correlationId, context);
        this.operation = operation;
        this.timeoutMs = timeoutMs;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                operation: this.operation,
                timeoutMs: this.timeoutMs,
            },
        };
    }
}
exports.TimeoutError = TimeoutError;
class ConfigurationError extends MCPError {
    constructor(message, configKey, expectedType, correlationId, context) {
        super(message, -32003, false, correlationId, context);
        this.configKey = configKey;
        this.expectedType = expectedType;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                configKey: this.configKey,
                expectedType: this.expectedType,
            },
        };
    }
}
exports.ConfigurationError = ConfigurationError;
class ResourceLimitError extends MCPError {
    constructor(resource, limit, current, correlationId, context) {
        const message = `${resource} limit exceeded: ${current}/${limit}`;
        super(message, -32004, true, correlationId, context);
        this.resource = resource;
        this.limit = limit;
        this.current = current;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                resource: this.resource,
                limit: this.limit,
                current: this.current,
            },
        };
    }
}
exports.ResourceLimitError = ResourceLimitError;
class InternalServerError extends MCPError {
    constructor(message, correlationId, context) {
        super(message, -32603, false, correlationId, context);
    }
}
exports.InternalServerError = InternalServerError;
class DependencyError extends MCPError {
    constructor(dependency, message, correlationId, context) {
        const errorMessage = message || `Required dependency '${dependency}' is not available`;
        super(errorMessage, -32006, false, correlationId, context);
        this.dependency = dependency;
    }
    toJSONRPC() {
        const base = super.toJSONRPC();
        return {
            ...base,
            data: {
                ...base.data,
                dependency: this.dependency,
            },
        };
    }
}
exports.DependencyError = DependencyError;
class MCPErrorFactory {
    static fromError(error, correlationId, context) {
        if (error instanceof MCPError) {
            return error;
        }
        return new InternalServerError(error.message || 'Unknown error occurred', correlationId, {
            ...context,
            originalError: error.name,
            originalStack: error.stack,
        });
    }
    static validation(field, value, expectedType, correlationId) {
        const message = expectedType
            ? `Invalid '${field}': expected ${expectedType}, got ${typeof value}`
            : `Invalid '${field}': ${value}`;
        return new ValidationError(message, field, value, correlationId, {
            expectedType,
        });
    }
    static toolError(toolName, operation, message, recoverable = true, correlationId) {
        return new ToolError(message, toolName, operation, recoverable, correlationId, { toolName, operation });
    }
    static notFound(resourceType, resourceId, correlationId) {
        return new NotFoundError(resourceType, resourceId, correlationId);
    }
    static rateLimit(limit, windowMs, resetTime, correlationId) {
        return new RateLimitError(limit, windowMs, resetTime, correlationId);
    }
    static timeout(operation, timeoutMs, correlationId) {
        return new TimeoutError(operation, timeoutMs, correlationId);
    }
    static config(configKey, message, expectedType, correlationId) {
        return new ConfigurationError(message, configKey, expectedType, correlationId);
    }
    static resourceLimit(resource, limit, current, correlationId) {
        return new ResourceLimitError(resource, limit, current, correlationId);
    }
    static dependency(dependency, message, correlationId) {
        return new DependencyError(dependency, message, correlationId);
    }
}
exports.MCPErrorFactory = MCPErrorFactory;
exports.ErrorCodes = {
    PARSE_ERROR: -32700,
    INVALID_REQUEST: -32600,
    METHOD_NOT_FOUND: -32601,
    INVALID_PARAMS: -32602,
    INTERNAL_ERROR: -32603,
    SERVER_ERROR_BASE: -32000,
    RATE_LIMIT_EXCEEDED: -32000,
    TOOL_ERROR: -32001,
    TIMEOUT_ERROR: -32002,
    CONFIGURATION_ERROR: -32003,
    RESOURCE_LIMIT_ERROR: -32004,
    AUTH_ERROR: -32005,
    DEPENDENCY_ERROR: -32006,
};
function isMCPError(error) {
    return error instanceof MCPError;
}
function isRecoverableError(error) {
    return isMCPError(error) && error.recoverable;
}
//# sourceMappingURL=MCPErrors.js.map