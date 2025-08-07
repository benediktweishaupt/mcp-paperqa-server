"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.MCPLogger = void 0;
const winston_1 = __importStar(require("winston"));
const uuid_1 = require("uuid");
const MCPErrors_1 = require("../errors/MCPErrors");
class MCPLogger {
    constructor(config = {}) {
        this.performanceTracker = new Map();
        this.config = {
            level: 'info',
            enableConsole: true,
            enableFile: false,
            enableStructuredLogging: true,
            enablePerformanceLogging: true,
            enableRequestLogging: true,
            correlationIdHeader: 'x-correlation-id',
            sensitiveFields: ['password', 'token', 'secret', 'key', 'authorization'],
            ...config,
        };
        this.logger = this.createWinstonLogger();
    }
    createWinstonLogger() {
        const logFormat = this.config.enableStructuredLogging
            ? this.createStructuredFormat()
            : winston_1.format.simple();
        const logTransports = [];
        if (this.config.enableConsole) {
            logTransports.push(new winston_1.transports.Console({
                format: winston_1.format.combine(winston_1.format.colorize(), winston_1.format.timestamp(), logFormat),
            }));
        }
        if (this.config.enableFile && this.config.fileOptions) {
            logTransports.push(new winston_1.transports.File({
                ...this.config.fileOptions,
                format: winston_1.format.combine(winston_1.format.timestamp(), logFormat),
            }));
        }
        return winston_1.default.createLogger({
            level: this.config.level,
            transports: logTransports,
            exitOnError: false,
            exceptionHandlers: this.config.enableFile && this.config.fileOptions
                ? [
                    new winston_1.transports.File({
                        filename: this.config.fileOptions.filename.replace('.log', '-exceptions.log'),
                    }),
                ]
                : [],
            rejectionHandlers: this.config.enableFile && this.config.fileOptions
                ? [
                    new winston_1.transports.File({
                        filename: this.config.fileOptions.filename.replace('.log', '-rejections.log'),
                    }),
                ]
                : [],
        });
    }
    createStructuredFormat() {
        return winston_1.format.printf((info) => {
            const { timestamp, level, message, ...meta } = info;
            const logEntry = {
                timestamp,
                level: level.toUpperCase(),
                message,
                ...this.sanitizeLogData(meta),
            };
            return JSON.stringify(logEntry);
        });
    }
    sanitizeLogData(data) {
        const sanitized = { ...data };
        for (const field of this.config.sensitiveFields) {
            if (field in sanitized) {
                sanitized[field] = '[REDACTED]';
            }
        }
        for (const [key, value] of Object.entries(sanitized)) {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                sanitized[key] = this.sanitizeLogData(value);
            }
        }
        return sanitized;
    }
    generateCorrelationId() {
        return `mcp-${(0, uuid_1.v4)()}`;
    }
    error(message, error, context) {
        const logData = {
            ...context,
            message,
        };
        if (error) {
            if (error instanceof MCPErrors_1.MCPError) {
                logData.error = error.toLogFormat();
            }
            else {
                logData.error = {
                    name: error.name,
                    message: error.message,
                    stack: error.stack,
                };
            }
        }
        this.logger.error(logData);
    }
    warn(message, context) {
        this.logger.warn({
            message,
            ...context,
        });
    }
    info(message, context) {
        this.logger.info({
            message,
            ...context,
        });
    }
    debug(message, context) {
        this.logger.debug({
            message,
            ...context,
        });
    }
    logRequestStart(method, correlationId, params) {
        if (!this.config.enableRequestLogging)
            return;
        this.info('Request started', {
            correlationId,
            method,
            operation: 'request_start',
            metadata: { params: this.sanitizeLogData({ params }) },
        });
    }
    logRequestEnd(method, correlationId, success, duration, result, error) {
        if (!this.config.enableRequestLogging)
            return;
        const logData = {
            correlationId,
            method,
            operation: 'request_end',
            duration,
            metadata: {
                success,
                result: success ? this.sanitizeLogData({ result }) : undefined,
            },
        };
        if (success) {
            this.info('Request completed successfully', logData);
        }
        else {
            this.error('Request failed', error, logData);
        }
    }
    startPerformanceTracking(operation, context) {
        if (!this.config.enablePerformanceLogging)
            return '';
        const trackingId = (0, uuid_1.v4)();
        this.performanceTracker.set(trackingId, {
            startTime: new Date(),
            operation,
            context: context,
        });
        this.debug('Performance tracking started', {
            ...context,
            operation,
            metadata: { ...context?.metadata, trackingId },
        });
        return trackingId;
    }
    endPerformanceTracking(trackingId, success = true, error, additionalMetrics) {
        if (!this.config.enablePerformanceLogging)
            return null;
        const tracking = this.performanceTracker.get(trackingId);
        if (!tracking) {
            this.warn('Performance tracking not found', {
                metadata: { trackingId }
            });
            return null;
        }
        this.performanceTracker.delete(trackingId);
        const endTime = new Date();
        const duration = endTime.getTime() - tracking.startTime.getTime();
        const metrics = {
            operation: tracking.operation,
            duration,
            startTime: tracking.startTime,
            endTime,
            success,
            errorType: error?.name,
            memoryUsage: process.memoryUsage(),
        };
        const logContext = {
            ...tracking.context,
            operation: 'performance_metrics',
            duration,
            metadata: {
                ...additionalMetrics,
                metrics,
            },
        };
        if (success) {
            this.info(`Performance: ${tracking.operation} completed in ${duration}ms`, logContext);
        }
        else {
            this.warn(`Performance: ${tracking.operation} failed after ${duration}ms`, logContext);
        }
        return metrics;
    }
    logToolExecution(toolName, operation, success, duration, correlationId, error, args) {
        const context = {
            correlationId,
            toolName,
            operation,
            duration,
            metadata: {
                success,
                arguments: this.sanitizeLogData(args || {}),
            },
        };
        if (success) {
            this.info(`Tool execution: ${toolName}.${operation} completed`, context);
        }
        else {
            this.error(`Tool execution: ${toolName}.${operation} failed`, error, context);
        }
    }
    logServerEvent(event, data) {
        this.info(`Server event: ${event}`, {
            operation: 'server_event',
            metadata: this.sanitizeLogData(data || {}),
        });
    }
    logProtocolEvent(event, correlationId, data) {
        this.info(`Protocol event: ${event}`, {
            correlationId,
            operation: 'protocol_event',
            metadata: this.sanitizeLogData(data || {}),
        });
    }
    child(defaultContext) {
        const childLogger = new MCPLogger(this.config);
        const originalError = childLogger.error.bind(childLogger);
        const originalWarn = childLogger.warn.bind(childLogger);
        const originalInfo = childLogger.info.bind(childLogger);
        const originalDebug = childLogger.debug.bind(childLogger);
        childLogger.error = (message, error, context) => {
            return originalError(message, error, { ...defaultContext, ...context });
        };
        childLogger.warn = (message, context) => {
            return originalWarn(message, { ...defaultContext, ...context });
        };
        childLogger.info = (message, context) => {
            return originalInfo(message, { ...defaultContext, ...context });
        };
        childLogger.debug = (message, context) => {
            return originalDebug(message, { ...defaultContext, ...context });
        };
        return childLogger;
    }
    setLogLevel(level) {
        this.config.level = level;
        this.logger.level = level;
    }
    getConfig() {
        return { ...this.config };
    }
    getStats() {
        return {
            activePerformanceTracking: this.performanceTracker.size,
            logLevel: this.logger.level,
            transportsCount: this.logger.transports.length,
        };
    }
    cleanup() {
        this.performanceTracker.clear();
        this.logger.close();
    }
}
exports.MCPLogger = MCPLogger;
//# sourceMappingURL=Logger.js.map