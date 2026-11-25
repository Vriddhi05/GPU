import { defineConfig, devices } from '@playwright/test';
const python = process.platform === 'win32' ? '.\\.venv\\Scripts\\python.exe' : '.venv/bin/python';
export default defineConfig({ testDir: './e2e', fullyParallel: false, reporter: 'list', use: { baseURL: 'http://127.0.0.1:3000', ...devices['Desktop Chrome'], screenshot: 'only-on-failure' }, webServer: [{ command: `${python} -m uvicorn backend.main:app --port 8000`, port: 8000, reuseExistingServer: !process.env.CI }, { command: 'npm run dev', port: 3000, reuseExistingServer: !process.env.CI }], outputDir: 'test-results/' });
