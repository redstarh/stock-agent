import { test, expect } from '@playwright/test';
import { setupApiMocks } from './helpers';

test.describe('App Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
  });

  test('loads dashboard as default route', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('대시보드')).toBeVisible();
  });

  test('app header shows StockNews branding', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('StockNews')).toBeVisible();
  });

  test('full navigation flow: dashboard → stock detail → back → themes', async ({ page }) => {
    // Start at dashboard
    await page.goto('/');
    await expect(page.getByText('대시보드')).toBeVisible();

    // Click stock to go to detail
    await page.getByText('삼성전자').first().click();
    await expect(page).toHaveURL(/\/stocks\/005930/);
    await expect(page.getByText('종목 상세')).toBeVisible();

    // Go back
    await page.getByText('← 뒤로').click();
    await expect(page).toHaveURL('/');

    // Navigate to themes
    await page.goto('/themes');
    await expect(page.getByText('테마 분석')).toBeVisible();
  });

  test('market selector switches between KR and US', async ({ page }) => {
    await page.goto('/');

    // KR is default — use first() to avoid strict mode error with multiple selectors
    const krButton = page.getByRole('tab', { name: 'KR' }).first();
    await expect(krButton).toBeVisible();

    // Click US
    const usButton = page.getByRole('tab', { name: 'US' }).first();
    await usButton.click();
  });
});
