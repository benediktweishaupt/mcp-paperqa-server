"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MCPStreamHandler = void 0;
const events_1 = require("events");
const stream_1 = require("stream");
class MCPStreamHandler extends events_1.EventEmitter {
    constructor(config = {}) {
        super();
        this.activeStreams = new Map();
        this.streamIdCounter = 0;
        this.config = {
            chunkSize: 64 * 1024,
            maxConcurrentStreams: 5,
            streamTimeout: 300000,
            compressionEnabled: false,
            enableProgress: true,
            ...config,
        };
    }
    createOutputStream(data, metadata) {
        const streamId = this.generateStreamId();
        if (this.activeStreams.size >= this.config.maxConcurrentStreams) {
            throw new Error('Maximum concurrent streams exceeded');
        }
        const serializedData = this.serializeData(data);
        const chunks = this.chunkData(serializedData);
        const stream = {
            id: streamId,
            startTime: new Date(),
            chunksReceived: 0,
            totalChunks: chunks.length,
            data: chunks,
            timeout: this.createStreamTimeout(streamId),
            completed: false,
        };
        this.activeStreams.set(streamId, stream);
        this.sendChunks(streamId, chunks, metadata);
        return streamId;
    }
    async processChunk(chunk) {
        const { id, sequence, data, isLast, totalChunks } = chunk;
        let stream = this.activeStreams.get(id);
        if (!stream) {
            stream = {
                id,
                startTime: new Date(),
                chunksReceived: 0,
                totalChunks: totalChunks,
                data: [],
                timeout: this.createStreamTimeout(id),
                completed: false,
            };
            this.activeStreams.set(id, stream);
        }
        if (sequence !== stream.chunksReceived) {
            throw new Error(`Invalid chunk sequence. Expected ${stream.chunksReceived}, got ${sequence}`);
        }
        stream.data[sequence] = data;
        stream.chunksReceived++;
        if (this.config.enableProgress && stream.totalChunks) {
            this.emit('progress', id, {
                current: stream.chunksReceived,
                total: stream.totalChunks,
            });
        }
        this.emit('chunk', chunk);
        if (isLast || (stream.totalChunks && stream.chunksReceived >= stream.totalChunks)) {
            await this.completeStream(id);
        }
    }
    getStreamData(streamId) {
        const stream = this.activeStreams.get(streamId);
        if (!stream || !stream.completed) {
            return null;
        }
        return this.reconstructData(stream.data);
    }
    cancelStream(streamId, reason) {
        const stream = this.activeStreams.get(streamId);
        if (!stream) {
            return false;
        }
        clearTimeout(stream.timeout);
        this.activeStreams.delete(streamId);
        this.emit('error', new Error(reason || 'Stream cancelled'), streamId);
        return true;
    }
    createReadableStream(data) {
        const chunks = this.chunkData(this.serializeData(data));
        let currentChunk = 0;
        return new stream_1.Readable({
            objectMode: true,
            read() {
                if (currentChunk < chunks.length) {
                    const chunk = {
                        id: 'readable-' + Date.now(),
                        sequence: currentChunk,
                        data: chunks[currentChunk],
                        isLast: currentChunk === chunks.length - 1,
                        totalChunks: chunks.length,
                    };
                    this.push(chunk);
                    currentChunk++;
                }
                else {
                    this.push(null);
                }
            },
        });
    }
    createWritableStream() {
        const chunks = [];
        let expectedSequence = 0;
        return new stream_1.Writable({
            objectMode: true,
            write: (chunk, _encoding, callback) => {
                try {
                    if (chunk.sequence !== expectedSequence) {
                        return callback(new Error(`Invalid chunk sequence. Expected ${expectedSequence}, got ${chunk.sequence}`));
                    }
                    chunks[chunk.sequence] = chunk.data;
                    expectedSequence++;
                    if (chunk.isLast) {
                        this.emit('data', this.reconstructData(chunks));
                        this.emit('end');
                    }
                    callback();
                }
                catch (error) {
                    callback(error);
                }
            },
        });
    }
    createTransformStream() {
        return new stream_1.Transform({
            objectMode: true,
            transform: (chunk, _encoding, callback) => {
                try {
                    const processedChunk = this.processChunkData(chunk);
                    callback(undefined, processedChunk);
                }
                catch (error) {
                    callback(error);
                }
            },
        });
    }
    getStreamStats() {
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
    cleanup() {
        const now = Date.now();
        for (const [id, stream] of this.activeStreams.entries()) {
            const age = now - stream.startTime.getTime();
            if (stream.completed || age > this.config.streamTimeout) {
                clearTimeout(stream.timeout);
                this.activeStreams.delete(id);
            }
        }
    }
    generateStreamId() {
        return `stream_${++this.streamIdCounter}_${Date.now()}`;
    }
    serializeData(data) {
        try {
            return JSON.stringify(data);
        }
        catch (error) {
            throw new Error(`Failed to serialize data: ${error.message}`);
        }
    }
    chunkData(data) {
        const chunks = [];
        const chunkSize = this.config.chunkSize;
        for (let i = 0; i < data.length; i += chunkSize) {
            chunks.push(data.slice(i, i + chunkSize));
        }
        return chunks.length > 0 ? chunks : [''];
    }
    reconstructData(chunks) {
        try {
            const serializedData = chunks.join('');
            return JSON.parse(serializedData);
        }
        catch (error) {
            throw new Error(`Failed to reconstruct data: ${error.message}`);
        }
    }
    processChunkData(chunk) {
        return chunk;
    }
    async sendChunks(streamId, chunks, metadata) {
        for (let i = 0; i < chunks.length; i++) {
            const chunk = {
                id: streamId,
                sequence: i,
                data: chunks[i],
                isLast: i === chunks.length - 1,
                totalChunks: chunks.length,
                metadata: i === 0 ? metadata : undefined,
            };
            this.emit('chunk', chunk);
            if (i < chunks.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 1));
            }
        }
    }
    async completeStream(streamId) {
        const stream = this.activeStreams.get(streamId);
        if (!stream) {
            return;
        }
        clearTimeout(stream.timeout);
        stream.completed = true;
        this.emit('completed', streamId, stream.chunksReceived);
        setTimeout(() => {
            this.activeStreams.delete(streamId);
        }, 30000);
    }
    createStreamTimeout(streamId) {
        return setTimeout(() => {
            this.cancelStream(streamId, 'Stream timeout');
        }, this.config.streamTimeout);
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    emit(event, ...args) {
        return super.emit(event, ...args);
    }
    on(event, listener) {
        return super.on(event, listener);
    }
    off(event, listener) {
        return super.off(event, listener);
    }
}
exports.MCPStreamHandler = MCPStreamHandler;
//# sourceMappingURL=MCPStreamHandler.js.map