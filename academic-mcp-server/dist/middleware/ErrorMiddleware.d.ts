import { EventEmitter } from 'events';
import { MCPError } from '../errors/MCPErrors';
import { MCPLogger } from '../logging/Logger';
export type ErrorHandler = (error: MCPError, context: ErrorContext, recovery?: ErrorRecoveryStrategy) => Promise<ErrorHandlingResult>;
export interface ErrorContext {
    correlationId: string;
    requestId?: string;
    method?: string;
    operation?: string;
    timestamp: Date;
    retryCount: number;
    metadata?: Record<string, unknown>;
}
export interface ErrorHandlingResult {
    shouldRetry: boolean;
    retryAfterMs?: number;
    transformedError?: MCPError;
    recoveryAction?: string;
    additionalContext?: Record<string, unknown>;
}
export interface ErrorRecoveryStrategy {
    maxRetries: number;
    baseDelayMs: number;
    maxDelayMs: number;
    backoffMultiplier: number;
    jitterFactor: number;
    recoverableErrorTypes: string[];
}
export interface CircuitBreakerConfig {
    failureThreshold: number;
    resetTimeoutMs: number;
    monitoringWindowMs: number;
    minimumRequestThreshold: number;
}
declare enum CircuitBreakerState {
    CLOSED = "closed",
    OPEN = "open",
    HALF_OPEN = "half_open"
}
declare class CircuitBreaker {
    private config;
    private logger;
    private state;
    private failureCount;
    private requestCount;
    private _lastFailureTime;
    private nextAttemptTime;
    constructor(config: CircuitBreakerConfig, logger: MCPLogger);
    canExecute(): boolean;
    recordResult(success: boolean): void;
    private onSuccess;
    private onFailure;
    getStatus(): {
        state: CircuitBreakerState;
        failureCount: number;
        requestCount: number;
        failureRate: number;
        nextAttemptTime?: Date | undefined;
    };
    reset(): void;
}
export interface ErrorMiddlewareEvents {
    'error-handled': (error: MCPError, context: ErrorContext, result: ErrorHandlingResult) => void;
    'retry-attempted': (error: MCPError, context: ErrorContext, attempt: number) => void;
    'circuit-breaker-opened': (operation: string) => void;
    'circuit-breaker-closed': (operation: string) => void;
    'error-recovery-failed': (error: MCPError, context: ErrorContext) => void;
}
export interface ErrorMiddlewareConfig {
    enableRetries: boolean;
    enableCircuitBreaker: boolean;
    defaultRecoveryStrategy: ErrorRecoveryStrategy;
    circuitBreakerConfig: CircuitBreakerConfig;
    errorHandlers: Map<string, ErrorHandler>;
}
export declare class ErrorMiddleware extends EventEmitter {
    private config;
    private logger;
    private circuitBreakers;
    private retryAttempts;
    constructor(logger: MCPLogger, config?: Partial<ErrorMiddlewareConfig>);
    registerErrorHandler(errorType: string, handler: ErrorHandler): void;
    unregisterErrorHandler(errorType: string): boolean;
    handleError(error: Error | MCPError, context?: Partial<ErrorContext>): Promise<ErrorHandlingResult>;
    executeWithErrorHandling<T>(operation: () => Promise<T>, context?: Partial<ErrorContext>): Promise<T>;
    private defaultErrorHandling;
    private calculateRetryDelay;
    private getOrCreateCircuitBreaker;
    private delay;
    getCircuitBreakerStatus(operation: string): ReturnType<CircuitBreaker['getStatus']> | null;
    resetCircuitBreaker(operation: string): boolean;
    getStats(): {
        activeCircuitBreakers: number;
        totalErrorHandlers: number;
        circuitBreakerStatuses: Record<string, ReturnType<CircuitBreaker['getStatus']>>;
    };
    updateConfig(newConfig: Partial<ErrorMiddlewareConfig>): void;
    cleanup(): void;
    emit<K extends keyof ErrorMiddlewareEvents>(event: K, ...args: Parameters<ErrorMiddlewareEvents[K]>): boolean;
    on<K extends keyof ErrorMiddlewareEvents>(event: K, listener: ErrorMiddlewareEvents[K]): this;
    off<K extends keyof ErrorMiddlewareEvents>(event: K, listener: ErrorMiddlewareEvents[K]): this;
}
export {};
//# sourceMappingURL=ErrorMiddleware.d.ts.map