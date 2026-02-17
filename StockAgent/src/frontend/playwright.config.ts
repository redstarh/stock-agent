import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 테스트 설정
 */
export default defineConfig({
  testDir: './e2e',

  // 병렬 실행
  fullyParallel: true,

  // CI에서만 --only 금지
  forbidOnly: !!process.env.CI,

  // CI에서 2번 재시도
  retries: process.env.CI ? 2 : 0,

  // CI에서는 1 worker, 로컬에서는 CPU 절반
  workers: process.env.CI ? 1 : undefined,

  // HTML 리포트
  reporter: [
    ['html'],
    ['list'],
    ...(process.env.CI ? [['github']] : []),
  ],

  use: {
    // Base URL
    baseURL: 'http://localhost:3000',

    // 실패 시 trace 수집
    trace: 'on-first-retry',

    // 실패 시 스크린샷
    screenshot: 'only-on-failure',

    // 실패 시 비디오
    video: 'retain-on-failure',

    // 기본 타임아웃
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // 브라우저 설정
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // 개발 서버 자동 실행
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
