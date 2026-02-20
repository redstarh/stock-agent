import { test, expect } from '@playwright/test';
import { setupApiMocks } from './helpers';

test.describe('Stock Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/stocks/005930');
  });

  test('displays stock code and name', async ({ page }) => {
    await expect(page.getByText('종목 상세 — 005930')).toBeVisible();
  });

  test('shows news score breakdown', async ({ page }) => {
    // Main score displayed
    await expect(page.getByText('삼성전자').first()).toBeVisible();
    // Sub-scores visible
    await expect(page.getByText(/최신성/)).toBeVisible();
    await expect(page.getByText(/빈도/)).toBeVisible();
    await expect(page.getByText(/감성:/)).toBeVisible();
    await expect(page.getByText(/공시/)).toBeVisible();
  });

  test('shows score timeline section', async ({ page }) => {
    await expect(page.getByText('스코어 타임라인')).toBeVisible();
  });

  test('shows sentiment distribution section', async ({ page }) => {
    await expect(page.getByText('감성 분포')).toBeVisible();
  });

  test('back button navigates to previous page', async ({ page }) => {
    // First navigate to dashboard, then to stock detail
    await page.goto('/');
    await page.getByText('삼성전자').first().click();
    await expect(page).toHaveURL(/\/stocks\/005930/);

    await page.getByText('← 뒤로').click();
    await expect(page).toHaveURL('/');
  });
});
