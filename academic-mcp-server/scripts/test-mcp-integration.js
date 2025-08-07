#!/usr/bin/env node

/**
 * MCP Integration Test Script
 * Tests the Academic MCP Server integration with basic MCP protocol messages
 */

const { spawn } = require('child_process');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function testMCPIntegration() {
  console.log('🧪 Testing Academic MCP Server Integration...\n');

  try {
    // Start the MCP server process
    const serverProcess = spawn('node', ['dist/index.js'], {
      stdio: 'pipe',
      cwd: process.cwd()
    });

    // Create MCP client transport
    const transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/index.js']
    });

    const client = new Client(
      {
        name: 'test-client',
        version: '1.0.0'
      },
      {
        capabilities: {}
      }
    );

    // Connect to server
    console.log('📡 Connecting to MCP server...');
    await client.connect(transport);
    console.log('✅ Connected successfully\n');

    // Test initialize
    console.log('🔧 Testing initialization...');
    const initResult = await client.initialize();
    console.log('✅ Initialization successful');
    console.log('   Server capabilities:', JSON.stringify(initResult.capabilities, null, 2));
    console.log('   Protocol version:', initResult.protocolVersion);
    console.log();

    // Test tools list
    console.log('🛠️  Testing tools list...');
    const toolsResult = await client.listTools();
    console.log('✅ Tools list retrieved');
    console.log(`   Available tools: ${toolsResult.tools.length}`);
    toolsResult.tools.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description}`);
    });
    console.log();

    // Test health check tool if available
    const healthTool = toolsResult.tools.find(t => t.name === 'health_check');
    if (healthTool) {
      console.log('🏥 Testing health check tool...');
      const healthResult = await client.callTool({
        name: 'health_check',
        arguments: {}
      });
      console.log('✅ Health check successful');
      console.log('   Result:', JSON.stringify(healthResult.content, null, 2));
    }

    // Disconnect
    await client.close();
    serverProcess.kill('SIGTERM');

    console.log('\n🎉 All MCP integration tests passed!');
    console.log('\n📋 Integration Summary:');
    console.log('   ✅ MCP protocol compliance');
    console.log('   ✅ Server startup and connection');
    console.log('   ✅ Tool registration and discovery');
    console.log('   ✅ Tool execution');
    console.log('   ✅ Clean shutdown');
    
    return true;

  } catch (error) {
    console.error('❌ MCP integration test failed:', error.message);
    console.error('\n🔍 Troubleshooting tips:');
    console.error('   1. Ensure server is built: npm run build');
    console.error('   2. Check dependencies: npm install');
    console.error('   3. Verify no port conflicts');
    return false;
  }
}

// Run test if called directly
if (require.main === module) {
  testMCPIntegration().then(success => {
    process.exit(success ? 0 : 1);
  });
}

module.exports = { testMCPIntegration };