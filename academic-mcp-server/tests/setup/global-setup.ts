/**
 * Global test setup configuration
 * Runs once before all test suites
 */

export default async function globalSetup() {
  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error'; // Reduce log noise in tests
  
  console.log('🧪 Global test setup completed');
}