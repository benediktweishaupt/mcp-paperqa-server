import { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { ToolRegistration, ToolContext } from '../types';

/**
 * Health Check Tool
 * Provides server health and status information
 */
export const healthCheckTool: ToolRegistration = {
  metadata: {
    name: 'health_check',
    description: 'Check server health status and performance metrics',
    version: '1.0.0',
    category: 'system',
    tags: ['health', 'monitoring', 'system'],
    inputSchema: {
      type: 'object',
      properties: {
        includeDetails: {
          type: 'boolean',
          description: 'Include detailed system information',
        },
        checkConnectivity: {
          type: 'boolean', 
          description: 'Test external connectivity',
        },
      },
      required: [],
    },
  },
  
  async handler(
    args: Record<string, unknown>,
    context: ToolContext
  ): Promise<CallToolResult> {
    const includeDetails = args.includeDetails as boolean || false;
    const checkConnectivity = args.checkConnectivity as boolean || false;
    
    // Basic health info
    const healthData: Record<string, unknown> = {
      status: 'healthy',
      timestamp: context.timestamp.toISOString(),
      requestId: context.requestId,
      uptime: process.uptime(),
    };

    // Add detailed system info if requested
    if (includeDetails) {
      healthData.memory = process.memoryUsage();
      healthData.cpu = process.cpuUsage();
      healthData.platform = process.platform;
      healthData.nodeVersion = process.version;
      healthData.pid = process.pid;
    }

    // Test connectivity if requested
    if (checkConnectivity) {
      try {
        // Simple DNS resolution test
        const dns = await import('dns');
        await new Promise((resolve, reject) => {
          dns.lookup('google.com', (err) => {
            if (err) reject(err);
            else resolve(null);
          });
        });
        healthData.connectivity = 'ok';
      } catch (error) {
        healthData.connectivity = 'failed';
        healthData.connectivityError = (error as Error).message;
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(healthData, null, 2),
        },
      ],
    };
  },

  // Optional rate limiting
  rateLimit: {
    requests: 10,
    windowMs: 60000, // 1 minute
  },
};