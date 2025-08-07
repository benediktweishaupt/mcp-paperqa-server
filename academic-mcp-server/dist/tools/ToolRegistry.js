"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ToolRegistry = void 0;
const events_1 = require("events");
const ToolValidator_1 = require("./ToolValidator");
class ToolRegistry extends events_1.EventEmitter {
    constructor(config = {}) {
        super();
        this.tools = new Map();
        this.callCounts = new Map();
        this.config = {
            enableValidation: true,
            enablePermissions: false,
            enableRateLimit: false,
            maxTools: 100,
            defaultCategory: 'general',
            ...config,
        };
    }
    async registerTool(registration) {
        const { metadata } = registration;
        if (this.tools.size >= this.config.maxTools) {
            throw new Error(`Tool registry is full (max: ${this.config.maxTools})`);
        }
        if (this.tools.has(metadata.name)) {
            throw new Error(`Tool '${metadata.name}' is already registered`);
        }
        if (this.config.enableValidation) {
            const validationResult = ToolValidator_1.ToolValidator.validateRegistration(registration);
            if (!validationResult.valid) {
                this.emit('validation-failed', metadata.name, validationResult.errors);
                throw new Error(`Tool validation failed: ${validationResult.errors.join(', ')}`);
            }
            if (validationResult.warnings && validationResult.warnings.length > 0) {
                console.warn(`Tool '${metadata.name}' warnings:`, validationResult.warnings);
            }
        }
        if (!metadata.category) {
            metadata.category = this.config.defaultCategory;
        }
        this.tools.set(metadata.name, registration);
        this.emit('tool-registered', metadata.name, metadata);
        console.log(`Tool '${metadata.name}' registered successfully`);
    }
    async unregisterTool(name) {
        if (!this.tools.has(name)) {
            return false;
        }
        this.tools.delete(name);
        this.callCounts.delete(name);
        this.emit('tool-unregistered', name);
        console.log(`Tool '${name}' unregistered successfully`);
        return true;
    }
    getToolMetadata(name) {
        const registration = this.tools.get(name);
        return registration ? registration.metadata : null;
    }
    getAllToolsMetadata() {
        return Array.from(this.tools.values()).map(reg => reg.metadata);
    }
    getToolsByCategory(category) {
        return Array.from(this.tools.values())
            .filter(reg => reg.metadata.category === category)
            .map(reg => reg.metadata);
    }
    getToolsByTag(tag) {
        return Array.from(this.tools.values())
            .filter(reg => reg.metadata.tags?.includes(tag))
            .map(reg => reg.metadata);
    }
    searchTools(query) {
        const lowerQuery = query.toLowerCase();
        return Array.from(this.tools.values())
            .filter(reg => reg.metadata.name.toLowerCase().includes(lowerQuery) ||
            reg.metadata.description.toLowerCase().includes(lowerQuery))
            .map(reg => reg.metadata);
    }
    hasTools(name) {
        return this.tools.has(name);
    }
    getToolCount() {
        return this.tools.size;
    }
    getStats() {
        const tools = Array.from(this.tools.values());
        const categoryCounts = {};
        const deprecatedTools = [];
        const experimentalTools = [];
        for (const registration of tools) {
            const { metadata } = registration;
            const category = metadata.category || 'uncategorized';
            categoryCounts[category] = (categoryCounts[category] || 0) + 1;
            if (metadata.deprecated) {
                deprecatedTools.push(metadata.name);
            }
            if (metadata.experimental) {
                experimentalTools.push(metadata.name);
            }
        }
        return {
            totalTools: tools.length,
            categoryCounts,
            deprecatedTools,
            experimentalTools,
        };
    }
    async executeTool(name, args, context) {
        const registration = this.tools.get(name);
        if (!registration) {
            throw new Error(`Tool '${name}' not found`);
        }
        if (this.config.enableRateLimit && registration.rateLimit) {
            if (!this.checkRateLimit(name, registration.rateLimit)) {
                throw new Error(`Rate limit exceeded for tool '${name}'`);
            }
        }
        if (this.config.enableValidation) {
            const validationResult = ToolValidator_1.ToolValidator.validateArguments(args, registration.metadata.inputSchema);
            if (!validationResult.valid) {
                throw new Error(`Argument validation failed: ${validationResult.errors.join(', ')}`);
            }
        }
        if (this.config.enablePermissions && registration.permissions) {
            console.debug(`Permission check for tool '${name}' with permissions:`, registration.permissions);
        }
        this.emit('tool-called', name, context);
        try {
            const result = await registration.handler(args, context);
            return result;
        }
        catch (error) {
            this.emit('tool-error', name, error, context);
            throw error;
        }
    }
    checkRateLimit(name, rateLimit) {
        const now = Date.now();
        const callData = this.callCounts.get(name);
        if (!callData || now > callData.resetTime) {
            this.callCounts.set(name, {
                count: 1,
                resetTime: now + rateLimit.windowMs,
            });
            return true;
        }
        if (callData.count >= rateLimit.requests) {
            return false;
        }
        callData.count += 1;
        this.callCounts.set(name, callData);
        return true;
    }
    clear() {
        const toolNames = Array.from(this.tools.keys());
        this.tools.clear();
        this.callCounts.clear();
        for (const name of toolNames) {
            this.emit('tool-unregistered', name);
        }
        console.log('All tools cleared from registry');
    }
    validateAllTools() {
        const results = {};
        for (const [name, registration] of this.tools.entries()) {
            results[name] = ToolValidator_1.ToolValidator.validateRegistration(registration);
        }
        return results;
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
exports.ToolRegistry = ToolRegistry;
//# sourceMappingURL=ToolRegistry.js.map