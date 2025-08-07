import { EventEmitter } from 'events';
export interface ServerState {
    isRunning: boolean;
    connections: Map<string, unknown>;
    registeredTools: Set<string>;
    startTime: Date;
}
export interface AcademicMCPServerOptions {
    name: string;
    version: string;
    description?: string;
    enableHealthCheck?: boolean;
    maxConnections?: number;
}
export declare class AcademicMCPServer extends EventEmitter {
    private server;
    private transport;
    private state;
    private options;
    private shutdownHandlers;
    constructor(options: AcademicMCPServerOptions);
    private setupServerHandlers;
    private setupEventHandlers;
    private handleToolCall;
    private handleHealthCheck;
    start(): Promise<void>;
    stop(): Promise<void>;
    addShutdownHandler(handler: () => Promise<void>): void;
    getState(): Readonly<ServerState>;
    getOptions(): Readonly<AcademicMCPServerOptions>;
    isRunning(): boolean;
    getUptime(): number;
}
//# sourceMappingURL=AcademicMCPServer.d.ts.map