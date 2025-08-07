import { EventEmitter } from 'events';
import { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import {
  ToolRegistration,
  ToolMetadata,
  ToolContext,
  ToolValidationResult,
  ToolRegistryConfig,
  ToolRegistryEvents,
} from './types';
import { ToolValidator } from './ToolValidator';

/**
 * Tool Registry for managing MCP tools
 * Handles registration, validation, discovery, and execution of tools
 */
export class ToolRegistry extends EventEmitter {
  private tools = new Map<string, ToolRegistration>();
  private config: ToolRegistryConfig;
  private callCounts = new Map<string, { count: number; resetTime: number }>();

  constructor(config: Partial<ToolRegistryConfig> = {}) {
    super();
    
    this.config = {
      enableValidation: true,
      enablePermissions: false,
      enableRateLimit: false,
      maxTools: 100,
      defaultCategory: 'general',
      ...config,
    };

    // Type the event emitter - removed to avoid TypeScript issues
  }

  /**
   * Register a new tool
   */
  async registerTool(registration: ToolRegistration): Promise<void> {
    const { metadata } = registration;

    // Check if registry is full
    if (this.tools.size >= this.config.maxTools) {
      throw new Error(`Tool registry is full (max: ${this.config.maxTools})`);
    }

    // Check if tool already exists
    if (this.tools.has(metadata.name)) {
      throw new Error(`Tool '${metadata.name}' is already registered`);
    }

    // Validate registration if enabled
    if (this.config.enableValidation) {
      const validationResult = ToolValidator.validateRegistration(registration);
      if (!validationResult.valid) {
        this.emit('validation-failed', metadata.name, validationResult.errors);
        throw new Error(`Tool validation failed: ${validationResult.errors.join(', ')}`);
      }

      if (validationResult.warnings && validationResult.warnings.length > 0) {
        console.warn(`Tool '${metadata.name}' warnings:`, validationResult.warnings);
      }
    }

    // Set default category if not provided
    if (!metadata.category) {
      metadata.category = this.config.defaultCategory;
    }

    // Store the tool
    this.tools.set(metadata.name, registration);

    // Emit registration event
    this.emit('tool-registered', metadata.name, metadata);

    console.log(`Tool '${metadata.name}' registered successfully`);
  }

  /**
   * Unregister a tool
   */
  async unregisterTool(name: string): Promise<boolean> {
    if (!this.tools.has(name)) {
      return false;
    }

    this.tools.delete(name);
    this.callCounts.delete(name);

    this.emit('tool-unregistered', name);
    console.log(`Tool '${name}' unregistered successfully`);

    return true;
  }

  /**
   * Get tool metadata
   */
  getToolMetadata(name: string): ToolMetadata | null {
    const registration = this.tools.get(name);
    return registration ? registration.metadata : null;
  }

  /**
   * Get all registered tools metadata
   */
  getAllToolsMetadata(): ToolMetadata[] {
    return Array.from(this.tools.values()).map(reg => reg.metadata);
  }

  /**
   * Get tools by category
   */
  getToolsByCategory(category: string): ToolMetadata[] {
    return Array.from(this.tools.values())
      .filter(reg => reg.metadata.category === category)
      .map(reg => reg.metadata);
  }

  /**
   * Get tools by tag
   */
  getToolsByTag(tag: string): ToolMetadata[] {
    return Array.from(this.tools.values())
      .filter(reg => reg.metadata.tags?.includes(tag))
      .map(reg => reg.metadata);
  }

  /**
   * Search tools by name or description
   */
  searchTools(query: string): ToolMetadata[] {
    const lowerQuery = query.toLowerCase();
    return Array.from(this.tools.values())
      .filter(reg => 
        reg.metadata.name.toLowerCase().includes(lowerQuery) ||
        reg.metadata.description.toLowerCase().includes(lowerQuery)
      )
      .map(reg => reg.metadata);
  }

  /**
   * Check if tool exists
   */
  hasTools(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Get tool count
   */
  getToolCount(): number {
    return this.tools.size;
  }

  /**
   * Get registry statistics
   */
  getStats(): {
    totalTools: number;
    categoryCounts: Record<string, number>;
    deprecatedTools: string[];
    experimentalTools: string[];
  } {
    const tools = Array.from(this.tools.values());
    const categoryCounts: Record<string, number> = {};
    const deprecatedTools: string[] = [];
    const experimentalTools: string[] = [];

    for (const registration of tools) {
      const { metadata } = registration;
      
      // Count by category
      const category = metadata.category || 'uncategorized';
      categoryCounts[category] = (categoryCounts[category] || 0) + 1;

      // Track deprecated tools
      if (metadata.deprecated) {
        deprecatedTools.push(metadata.name);
      }

      // Track experimental tools
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

  /**
   * Execute a tool
   */
  async executeTool(
    name: string,
    args: Record<string, unknown>,
    context: ToolContext
  ): Promise<CallToolResult> {
    const registration = this.tools.get(name);
    if (!registration) {
      throw new Error(`Tool '${name}' not found`);
    }

    // Check rate limit
    if (this.config.enableRateLimit && registration.rateLimit) {
      if (!this.checkRateLimit(name, registration.rateLimit)) {
        throw new Error(`Rate limit exceeded for tool '${name}'`);
      }
    }

    // Validate arguments if validation is enabled
    if (this.config.enableValidation) {
      const validationResult = ToolValidator.validateArguments(args, registration.metadata.inputSchema);
      if (!validationResult.valid) {
        throw new Error(`Argument validation failed: ${validationResult.errors.join(', ')}`);
      }
    }

    // Check permissions
    if (this.config.enablePermissions && registration.permissions) {
      // Placeholder for permission checking - would integrate with auth system
      // For now, just log permission check
      console.debug(`Permission check for tool '${name}' with permissions:`, registration.permissions);
    }

    // Emit tool called event
    this.emit('tool-called', name, context);

    try {
      // Execute the tool
      const result = await registration.handler(args, context);
      return result;
    } catch (error) {
      this.emit('tool-error', name, error as Error, context);
      throw error;
    }
  }

  /**
   * Check rate limit for a tool
   */
  private checkRateLimit(name: string, rateLimit: { requests: number; windowMs: number }): boolean {
    const now = Date.now();
    const callData = this.callCounts.get(name);

    if (!callData || now > callData.resetTime) {
      // Reset or initialize call count
      this.callCounts.set(name, {
        count: 1,
        resetTime: now + rateLimit.windowMs,
      });
      return true;
    }

    if (callData.count >= rateLimit.requests) {
      return false;
    }

    // Increment call count
    callData.count += 1;
    this.callCounts.set(name, callData);
    return true;
  }

  /**
   * Clear all tools
   */
  clear(): void {
    const toolNames = Array.from(this.tools.keys());
    this.tools.clear();
    this.callCounts.clear();

    for (const name of toolNames) {
      this.emit('tool-unregistered', name);
    }

    console.log('All tools cleared from registry');
  }

  /**
   * Validate all registered tools
   */
  validateAllTools(): Record<string, ToolValidationResult> {
    const results: Record<string, ToolValidationResult> = {};

    for (const [name, registration] of this.tools.entries()) {
      results[name] = ToolValidator.validateRegistration(registration);
    }

    return results;
  }

  /**
   * Get configuration
   */
  getConfig(): Readonly<ToolRegistryConfig> {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<ToolRegistryConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }


  /**
   * Typed event emitter methods
   */
  emit<K extends keyof ToolRegistryEvents>(
    event: K,
    ...args: Parameters<ToolRegistryEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  on<K extends keyof ToolRegistryEvents>(
    event: K,
    listener: ToolRegistryEvents[K]
  ): this {
    return super.on(event, listener);
  }

  off<K extends keyof ToolRegistryEvents>(
    event: K,
    listener: ToolRegistryEvents[K]
  ): this {
    return super.off(event, listener);
  }
}