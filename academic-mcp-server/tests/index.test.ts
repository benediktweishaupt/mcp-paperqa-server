/**
 * Basic tests for project setup validation
 */

describe('Project Setup', () => {
  test('should be able to import main index file', async () => {
    // This test ensures our TypeScript setup is working correctly
    const indexModule = await import('../src/index');
    expect(indexModule).toBeDefined();
  });

  test('environment should be test', () => {
    expect(process.env.NODE_ENV).toBe('test');
  });
});