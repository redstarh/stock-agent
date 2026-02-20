import { test, expect } from '@playwright/test';
import { setupApiMocks, mockTopNews } from './helpers';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/');
  });

  test('displays dashboard header', async ({ page }) => {
    await expect(page.getByText('대시보드')).toBeVisible();
  });

  test('shows top stock cards with scores', async ({ page }) => {
    for (const item of mockTopNews) {
      await expect(page.getByText(item.stock_name!).first()).toBeVisible();
    }
  });

  test('shows theme strength section', async ({ page }) => {
    await expect(page.getByText('테마 강도')).toBeVisible();
  });

  test('navigates to stock detail on card click', async ({ page }) => {
    await page.getByText('삼성전자').first().click();
    await expect(page).toHaveURL(/\/stocks\/005930/);
    await expect(page.getByText('종목 상세')).toBeVisible();
  });
});
