import { MCPError } from '../errors/MCPErrors';
export type LogLevel = 'error' | 'warn' | 'info' | 'debug';
export interface LogContext {
    correlationId?: string;
    requestId?: string;
    toolName?: string;
    method?: string;
    userId?: string;
    sessionId?: string;
    operation?: string;
    duration?: number;
    metadata?: Record<string, unknown>;
}
export interface PerformanceMetrics {
    operation: string;
    duration: number;
    startTime: Date;
    endTime: Date;
    success: boolean;
    errorType?: string;
    memoryUsage?: {
        heapUsed: number;
        heapTotal: number;
        external: number;
        rss: number;
    };
}
export interface LoggerConfig {
    level: LogLevel;
    enableConsole: boolean;
    enableFile: boolean;
    fileOptions?: {
        filename: string;
        maxsize: number;
        maxFiles: number;
    };
    enableStructuredLogging: boolean;
    enablePerformanceLogging: boolean;
    enableRequestLogging: boolean;
    correlationIdHeader?: string;
    sensitiveFields: string[];
}
export declare class MCPLogger {
    private logger;
    private config;
    private performanceTracker;
    constructor(config?: Partial<LoggerConfig>);
    private createWinstonLogger;
    private createStructuredFormat;
    private sanitizeLogData;
    generateCorrelationId(): string;
    error(message: string, error?: Error | MCPError, context?: LogContext): void;
    warn(message: string, context?: LogContext): void;
    info(message: string, context?: LogContext): void;
    debug(message: string, context?: LogContext): void;
    logRequestStart(method: string, correlationId: string, params?: unknown): void;
    logRequestEnd(method: string, correlationId: string, success: boolean, duration: number, result?: unknown, error?: Error): void;
    startPerformanceTracking(operation: string, context?: LogContext): string;
    endPerformanceTracking(trackingId: string, success?: boolean, error?: Error, additionalMetrics?: Record<string, unknown>): PerformanceMetrics | null;
    logToolExecution(toolName: string, operation: string, success: boolean, duration: number, correlationId?: string, error?: Error, args?: Record<string, unknown>): void;
    logServerEvent(event: string, data?: Record<string, unknown>): void;
    logProtocolEvent(event: string, correlationId?: string, data?: Record<string, unknown>): void;
    child(defaultContext: LogContext): MCPLogger;
    setLogLevel(level: LogLevel): void;
    getConfig(): Readonly<LoggerConfig>;
    getStats(): {
        activePerformanceTracking: number;
        logLevel: string;
        transportsCount: number;
    };
    cleanup(): void;
}
//# sourceMappingURL=Logger.d.ts.map