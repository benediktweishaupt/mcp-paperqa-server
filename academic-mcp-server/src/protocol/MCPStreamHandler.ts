import { EventEmitter } from 'events';
import { Readable, Writable, Transform } from 'stream';

/**
 * Stream Chunk Types
 */
export interface StreamChunk {
  id: string;
  sequence: number;
  data: unknown;
  isLast: boolean;
  totalChunks?: number;
  metadata?: Record<string, unknown> | undefined;
}

/**
 * Stream Events
 */
export interface MCPStreamEvents {
  'chunk': (chunk: StreamChunk) => void;
  'completed': (streamId: string, totalChunks: number) => void;
  'error': (error: Error, streamId?: string) => void;
  'progress': (streamId: string, progress: { current: number; total?: number }) => void;
  'data': (data: unknown) => void;
  'end': () => void;
}

/**
 * Stream Configuration
 */
export interface StreamConfig {
  chunkSize: number; // Maximum size per chunk in bytes
  maxConcurrentStreams: number;
  streamTimeout: number; // Timeout per stream in ms
  compressionEnabled: boolean;
  enableProgress: boolean;
}

/**
 * Active Stream Information
 */
interface ActiveStream {
  id: string;
  startTime: Date;
  chunksReceived: number;
  totalChunks?: number | undefined;
  data: unknown[];
  timeout: NodeJS.Timeout;
  completed: boolean;
}

/**
 * MCP Stream Handler
 * Handles bidirectional streaming for large MCP responses
 */
export class MCPStreamHandler extends EventEmitter {
  private config: StreamConfig;
  private activeStreams = new Map<string, ActiveStream>();
  private streamIdCounter = 0;

  constructor(config: Partial<StreamConfig> = {}) {
    super();
    
    this.config = {
      chunkSize: 64 * 1024, // 64KB chunks
      maxConcurrentStreams: 5,
      streamTimeout: 300000, // 5 minutes
      compressionEnabled: false,
      enableProgress: true,
      ...config,
    };
  }

  /**
   * Create a new stream for sending large data
   */
  createOutputStream(data: unknown, metadata?: Record<string, unknown>): string {
    const streamId = this.generateStreamId();
    
    // Check concurrent stream limit
    if (this.activeStreams.size >= this.config.maxConcurrentStreams) {
      throw new Error('Maximum concurrent streams exceeded');
    }

    // Serialize and chunk the data
    const serializedData = this.serializeData(data);
    const chunks = this.chunkData(serializedData);
    
    // Create stream info
    const stream: ActiveStream = {
      id: streamId,
      startTime: new Date(),
      chunksReceived: 0,
      totalChunks: chunks.length,
      data: chunks,
      timeout: this.createStreamTimeout(streamId),
      completed: false,
    };

    this.activeStreams.set(streamId, stream);

    // Start sending chunks
    this.sendChunks(streamId, chunks, metadata);

    return streamId;
  }

  /**
   * Process incoming stream chunk
   */
  async processChunk(chunk: StreamChunk): Promise<void> {
    const { id, sequence, data, isLast, totalChunks } = chunk;

    let stream = this.activeStreams.get(id);
    if (!stream) {
      // Create new stream for incoming data
      stream = {
        id,
        startTime: new Date(),
        chunksReceived: 0,
        totalChunks: totalChunks as number | undefined,
        data: [],
        timeout: this.createStreamTimeout(id),
        completed: false,
      };
      this.activeStreams.set(id, stream);
    }

    // Validate chunk sequence
    if (sequence !== stream.chunksReceived) {
      throw new Error(`Invalid chunk sequence. Expected ${stream.chunksReceived}, got ${sequence}`);
    }

    // Add chunk data
    stream.data[sequence] = data;
    stream.chunksReceived++;

    // Emit progress if enabled
    if (this.config.enableProgress && stream.totalChunks) {
      this.emit('progress', id, {
        current: stream.chunksReceived,
        total: stream.totalChunks,
      });
    }

    // Emit chunk event
    this.emit('chunk', chunk);

    // Check if stream is complete
    if (isLast || (stream.totalChunks && stream.chunksReceived >= stream.totalChunks)) {
      await this.completeStream(id);
    }
  }

  /**
   * Get completed stream data
   */
  getStreamData(streamId: string): unknown | null {
    const stream = this.activeStreams.get(streamId);
    if (!stream || !stream.completed) {
      return null;
    }

    // Reconstruct data from chunks
    return this.reconstructData(stream.data);
  }

  /**
   * Cancel an active stream
   */
  cancelStream(streamId: string, reason?: string): boolean {
    const stream = this.activeStreams.get(streamId);
    if (!stream) {
      return false;
    }

    // Clear timeout
    clearTimeout(stream.timeout);

    // Remove stream
    this.activeStreams.delete(streamId);

    // Emit error
    this.emit('error', new Error(reason || 'Stream cancelled'), streamId);

    return true;
  }

  /**
   * Create a readable stream for large data
   */
  createReadableStream(data: unknown): Readable {
    const chunks = this.chunkData(this.serializeData(data));
    let currentChunk = 0;

    return new Readable({
      objectMode: true,
      read() {
        if (currentChunk < chunks.length) {
          const chunk: StreamChunk = {
            id: 'readable-' + Date.now(),
            sequence: currentChunk,
            data: chunks[currentChunk],
            isLast: currentChunk === chunks.length - 1,
            totalChunks: chunks.length,
          };
          this.push(chunk);
          currentChunk++;
        } else {
          this.push(null); // End stream
        }
      },
    });
  }

  /**
   * Create a writable stream for receiving chunks
   */
  createWritableStream(): Writable {
    const chunks: unknown[] = [];
    let expectedSequence = 0;

    return new Writable({
      objectMode: true,
      write: (chunk: StreamChunk, _encoding: any, callback: (error?: Error) => void) => {
        try {
          // Validate sequence
          if (chunk.sequence !== expectedSequence) {
            return callback(new Error(`Invalid chunk sequence. Expected ${expectedSequence}, got ${chunk.sequence}`));
          }

          chunks[chunk.sequence] = chunk.data;
          expectedSequence++;

          // Check if complete
          if (chunk.isLast) {
            // Emit reconstructed data
            this.emit('data', this.reconstructData(chunks));
            this.emit('end');
          }

          callback();
        } catch (error) {
          callback(error as Error);
        }
      },
    });
  }

  /**
   * Create a transform stream for processing chunks
   */
  createTransformStream(): Transform {
    return new Transform({
      objectMode: true,
      transform: (chunk: StreamChunk, _encoding: any, callback: (error?: Error, processedChunk?: StreamChunk) => void) => {
        try {
          // Process chunk (could add compression, validation, etc.)
          const processedChunk = this.processChunkData(chunk);
          callback(undefined, processedChunk);
        } catch (error) {
          callback(error as Error);
        }
      },
    });
  }

  /**
   * Get stream statistics
   */
  getStreamStats(): {
    activeStreams: number;
    totalStreamsProcessed: number;
    averageChunkSize: number;
    longestStreamDuration: number;
  } {
    const activeCount = this.activeStreams.size;
    let totalDuration = 0;
    let longestDuration = 0;
    let totalChunks = 0;

    for (const stream of this.activeStreams.values()) {
      const duration = Date.now() - stream.startTime.getTime();
      totalDuration += duration;
      longestDuration = Math.max(longestDuration, duration);
      totalChunks += stream.chunksReceived;
    }

    return {
      activeStreams: activeCount,
      totalStreamsProcessed: this.streamIdCounter,
      averageChunkSize: totalChunks > 0 ? this.config.chunkSize : 0,
      longestStreamDuration: longestDuration,
    };
  }

  /**
   * Clean up completed or timed-out streams
   */
  cleanup(): void {
    const now = Date.now();
    
    for (const [id, stream] of this.activeStreams.entries()) {
      const age = now - stream.startTime.getTime();
      if (stream.completed || age > this.config.streamTimeout) {
        clearTimeout(stream.timeout);
        this.activeStreams.delete(id);
      }
    }
  }

  /**
   * Generate unique stream ID
   */
  private generateStreamId(): string {
    return `stream_${++this.streamIdCounter}_${Date.now()}`;
  }

  /**
   * Serialize data for streaming
   */
  private serializeData(data: unknown): string {
    try {
      return JSON.stringify(data);
    } catch (error) {
      throw new Error(`Failed to serialize data: ${(error as Error).message}`);
    }
  }

  /**
   * Chunk serialized data
   */
  private chunkData(data: string): string[] {
    const chunks: string[] = [];
    const chunkSize = this.config.chunkSize;

    for (let i = 0; i < data.length; i += chunkSize) {
      chunks.push(data.slice(i, i + chunkSize));
    }

    return chunks.length > 0 ? chunks : [''];
  }

  /**
   * Reconstruct data from chunks
   */
  private reconstructData(chunks: unknown[]): unknown {
    try {
      const serializedData = chunks.join('');
      return JSON.parse(serializedData);
    } catch (error) {
      throw new Error(`Failed to reconstruct data: ${(error as Error).message}`);
    }
  }

  /**
   * Process chunk data (for transform stream)
   */
  private processChunkData(chunk: StreamChunk): StreamChunk {
    // Add any processing logic here (compression, validation, etc.)
    return chunk;
  }

  /**
   * Send chunks for a stream
   */
  private async sendChunks(streamId: string, chunks: string[], metadata?: Record<string, unknown>): Promise<void> {
    for (let i = 0; i < chunks.length; i++) {
      const chunk: StreamChunk = {
        id: streamId,
        sequence: i,
        data: chunks[i],
        isLast: i === chunks.length - 1,
        totalChunks: chunks.length,
        metadata: i === 0 ? (metadata as Record<string, unknown> | undefined) : undefined, // Include metadata only in first chunk
      };

      // Emit chunk (transport layer should handle actual sending)
      this.emit('chunk', chunk);

      // Small delay to prevent overwhelming
      if (i < chunks.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1));
      }
    }
  }

  /**
   * Complete a stream
   */
  private async completeStream(streamId: string): Promise<void> {
    const stream = this.activeStreams.get(streamId);
    if (!stream) {
      return;
    }

    // Clear timeout
    clearTimeout(stream.timeout);

    // Mark as completed
    stream.completed = true;

    // Emit completion event
    this.emit('completed', streamId, stream.chunksReceived);

    // Auto-cleanup after a delay
    setTimeout(() => {
      this.activeStreams.delete(streamId);
    }, 30000); // Keep for 30 seconds for potential retrieval
  }

  /**
   * Create timeout for stream
   */
  private createStreamTimeout(streamId: string): NodeJS.Timeout {
    return setTimeout(() => {
      this.cancelStream(streamId, 'Stream timeout');
    }, this.config.streamTimeout);
  }

  /**
   * Get configuration
   */
  getConfig(): Readonly<StreamConfig> {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<StreamConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Typed event emitter methods
   */
  emit<K extends keyof MCPStreamEvents>(
    event: K,
    ...args: Parameters<MCPStreamEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  on<K extends keyof MCPStreamEvents>(
    event: K,
    listener: MCPStreamEvents[K]
  ): this {
    return super.on(event, listener);
  }

  off<K extends keyof MCPStreamEvents>(
    event: K,
    listener: MCPStreamEvents[K]
  ): this {
    return super.off(event, listener);
  }
}