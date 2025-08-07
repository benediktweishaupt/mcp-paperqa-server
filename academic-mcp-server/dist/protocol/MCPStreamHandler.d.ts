import { EventEmitter } from 'events';
import { Readable, Writable, Transform } from 'stream';
export interface StreamChunk {
    id: string;
    sequence: number;
    data: unknown;
    isLast: boolean;
    totalChunks?: number;
    metadata?: Record<string, unknown> | undefined;
}
export interface MCPStreamEvents {
    'chunk': (chunk: StreamChunk) => void;
    'completed': (streamId: string, totalChunks: number) => void;
    'error': (error: Error, streamId?: string) => void;
    'progress': (streamId: string, progress: {
        current: number;
        total?: number;
    }) => void;
    'data': (data: unknown) => void;
    'end': () => void;
}
export interface StreamConfig {
    chunkSize: number;
    maxConcurrentStreams: number;
    streamTimeout: number;
    compressionEnabled: boolean;
    enableProgress: boolean;
}
export declare class MCPStreamHandler extends EventEmitter {
    private config;
    private activeStreams;
    private streamIdCounter;
    constructor(config?: Partial<StreamConfig>);
    createOutputStream(data: unknown, metadata?: Record<string, unknown>): string;
    processChunk(chunk: StreamChunk): Promise<void>;
    getStreamData(streamId: string): unknown | null;
    cancelStream(streamId: string, reason?: string): boolean;
    createReadableStream(data: unknown): Readable;
    createWritableStream(): Writable;
    createTransformStream(): Transform;
    getStreamStats(): {
        activeStreams: number;
        totalStreamsProcessed: number;
        averageChunkSize: number;
        longestStreamDuration: number;
    };
    cleanup(): void;
    private generateStreamId;
    private serializeData;
    private chunkData;
    private reconstructData;
    private processChunkData;
    private sendChunks;
    private completeStream;
    private createStreamTimeout;
    getConfig(): Readonly<StreamConfig>;
    updateConfig(newConfig: Partial<StreamConfig>): void;
    emit<K extends keyof MCPStreamEvents>(event: K, ...args: Parameters<MCPStreamEvents[K]>): boolean;
    on<K extends keyof MCPStreamEvents>(event: K, listener: MCPStreamEvents[K]): this;
    off<K extends keyof MCPStreamEvents>(event: K, listener: MCPStreamEvents[K]): this;
}
//# sourceMappingURL=MCPStreamHandler.d.ts.map