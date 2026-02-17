import { test, expect } from '@playwright/test';
import { setupApiMocks, mockThemes } from './helpers';

test.describe('Theme Analysis Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/themes');
  });

  test('displays theme analysis header', async ({ page }) => {
    await expect(page.getByText('테마 분석')).toBeVisible();
  });

  test('shows theme strength chart section', async ({ page }) => {
    await expect(page.getByText('테마 강도 차트')).toBeVisible();
  });

  test('shows all themes in detail list', async ({ page }) => {
    for (const theme of mockThemes) {
      await expect(page.getByText(theme.theme).first()).toBeVisible();
    }
  });

  test('shows news count per theme', async ({ page }) => {
    for (const theme of mockThemes) {
      await expect(page.getByText(`뉴스 ${theme.news_count}건`)).toBeVisible();
    }
  });

  test('themes are sorted by strength score descending', async ({ page }) => {
    // Each theme item has a unique "뉴스 N건" — go up 2 levels to the full item row
    const newsCountLabels = page.getByText(/^뉴스 \d+건$/);
    await expect(newsCountLabels).toHaveCount(3);

    // xpath=../.. goes from <span> → <div> → theme item <div>
    await expect(newsCountLabels.nth(0).locator('xpath=../..')).toContainText('반도체');
    await expect(newsCountLabels.nth(1).locator('xpath=../..')).toContainText('2차전지');
    await expect(newsCountLabels.nth(2).locator('xpath=../..')).toContainText('AI/로봇');
  });
});
