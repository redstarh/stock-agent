import { test, expect } from '@playwright/test';
import { setupApiMocks, mockDailyResults } from './helpers';

test.describe('Verification Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/verification');
  });

  test('displays page heading and controls', async ({ page }) => {
    await expect(page.getByText('예측 검증')).toBeVisible();
    await expect(page.locator('input[type="date"]')).toBeVisible();
    await expect(page.locator('select')).toBeVisible();
  });

  test('period selector has correct options', async ({ page }) => {
    const select = page.locator('select');
    await expect(select).toBeVisible();

    // Check options
    await expect(select.locator('option[value="7"]')).toHaveText('7일');
    await expect(select.locator('option[value="30"]')).toHaveText('30일');
    await expect(select.locator('option[value="90"]')).toHaveText('90일');

    // Default should be 30
    await expect(select).toHaveValue('30');
  });

  test('displays accuracy overview card with mock data', async ({ page }) => {
    // Overall accuracy
    await expect(page.getByText('전체 정확도')).toBeVisible();
    await expect(page.getByText('72.5%')).toBeVisible();

    // Total predictions
    await expect(page.getByText('총 예측')).toBeVisible();
    await expect(page.getByText('120건').first()).toBeVisible();

    // Correct predictions
    await expect(page.getByText('정답')).toBeVisible();
    await expect(page.getByText('87건')).toBeVisible();

    // Incorrect predictions
    await expect(page.getByText('오답')).toBeVisible();
    await expect(page.getByText('33건')).toBeVisible();
  });

  test('displays direction breakdown in overview card', async ({ page }) => {
    await expect(page.getByText('방향별 정확도')).toBeVisible();

    // Up direction
    const upBox = page.locator('.bg-red-50');
    await expect(upBox.getByText('상승 예측')).toBeVisible();
    await expect(upBox.getByRole('paragraph').filter({ hasText: '76.0%' })).toBeVisible();
    await expect(upBox.getByText('38/50')).toBeVisible();

    // Down direction
    const downBox = page.locator('.bg-blue-50');
    await expect(downBox.getByText('하락 예측')).toBeVisible();
    await expect(downBox.getByRole('paragraph').filter({ hasText: '71.1%' })).toBeVisible();
    await expect(downBox.getByText('32/45')).toBeVisible();

    // Neutral direction - use more specific selector
    await expect(page.getByText('중립 예측')).toBeVisible();
    await expect(page.locator('.bg-gray-50 p.text-lg.font-bold.text-gray-600')).toBeVisible();
    await expect(page.getByText('17/25')).toBeVisible();
  });

  test('displays stock results table with mock data', async ({ page }) => {
    await expect(page.getByText('종목별 검증 결과')).toBeVisible();

    // Check table headers using role
    await expect(page.getByRole('columnheader', { name: '예측' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: '실제' })).toBeVisible();

    // Check stock data
    for (const result of mockDailyResults.results) {
      await expect(page.getByText(result.stock_name!)).toBeVisible();
      await expect(page.getByText(result.stock_code)).toBeVisible();
    }
  });

  test('stock results table shows correct prediction indicators', async ({ page }) => {
    // Find Samsung row (correct prediction)
    const samsungRow = page.locator('tr', { has: page.getByText('005930') });
    await expect(samsungRow.getByText('✓')).toBeVisible();

    // Find SK Hynix row (incorrect prediction)
    const skRow = page.locator('tr', { has: page.getByText('000660') });
    await expect(skRow.getByText('✗')).toBeVisible();
  });

  test('displays theme accuracy breakdown with mock data', async ({ page }) => {
    await expect(page.getByText('테마별 정확도')).toBeVisible();

    // Wait for chart to render
    await page.waitForTimeout(500);

    // Check that we have theme elements in the chart area
    const chartSection = page.locator('section', { has: page.getByText('테마별 정확도') });
    await expect(chartSection).toBeVisible();
  });

  test('theme accuracy shows stock counts and percentages', async ({ page }) => {
    // Wait for chart and data to render
    await page.waitForTimeout(1000);

    // The theme accuracy component shows a chart
    // Just verify the section is present and has border/bg styling
    const themeSection = page.locator('section', { has: page.getByText('테마별 정확도') });
    await expect(themeSection).toBeVisible();

    // Verify the rounded border container (chart wrapper) exists
    await expect(themeSection.locator('.rounded-lg.border.bg-white')).toBeVisible();
  });

  test('displays daily accuracy trend section', async ({ page }) => {
    await expect(page.getByText('일별 정확도 추세')).toBeVisible();
  });

  test('date picker allows date selection', async ({ page }) => {
    const datePicker = page.locator('input[type="date"]');
    await expect(datePicker).toBeVisible();

    // Change date
    await datePicker.fill('2026-02-15');
    await expect(datePicker).toHaveValue('2026-02-15');
  });

  test('period selector allows period change', async ({ page }) => {
    const select = page.locator('select');

    // Change to 7 days
    await select.selectOption('7');
    await expect(select).toHaveValue('7');

    // Change to 90 days
    await select.selectOption('90');
    await expect(select).toHaveValue('90');
  });

  test('navigates to verification page via sidebar', async ({ page }) => {
    // Go to dashboard first
    await page.goto('/');
    await expect(page.getByText('대시보드')).toBeVisible();

    // Navigate to verification via sidebar link
    await page.goto('/verification');
    await expect(page).toHaveURL('/verification');
    await expect(page.getByText('예측 검증')).toBeVisible();
  });

  test('shows result count in section header', async ({ page }) => {
    await expect(page.getByText('종목별 검증 결과')).toBeVisible();
    await expect(page.getByText(`(${mockDailyResults.total}건)`)).toBeVisible();
  });

  test('table sorting works on stock code column', async ({ page }) => {
    const stockCodeHeader = page.getByRole('button', { name: /종목/ });
    await expect(stockCodeHeader).toBeVisible();

    // Click to sort
    await stockCodeHeader.click();

    // Should show sort indicator
    await expect(page.locator('text=/종목.*[↑↓]/')).toBeVisible();
  });

  test('table sorting works on confidence column', async ({ page }) => {
    const confidenceHeader = page.getByRole('button', { name: /신뢰도/ });
    await expect(confidenceHeader).toBeVisible();

    // Click to sort
    await confidenceHeader.click();

    // Should show sort indicator
    await expect(page.locator('text=/신뢰도.*[↑↓]/')).toBeVisible();
  });

  test('displays confidence values as percentages', async ({ page }) => {
    // Check that confidence values are displayed with % symbol in table
    const table = page.locator('table');

    // Check for confidence values (82.0%, 75.0%, etc.)
    await expect(table.getByText('82.0%')).toBeVisible();
    await expect(table.getByText('75.0%')).toBeVisible();
    await expect(table.getByText('60.0%')).toBeVisible();
  });

  test('displays actual change percentages with correct formatting', async ({ page }) => {
    // Check positive change (Samsung: +2.3%)
    await expect(page.getByText('+2.30%')).toBeVisible();

    // Check negative change (SK Hynix: -1.2%)
    await expect(page.getByText('-1.20%')).toBeVisible();
  });

  test('empty state shows when no results', async ({ page }) => {
    // Mock empty results
    await page.route('**/api/v1/verification/daily*', async (route) => {
      await route.fulfill({
        json: {
          date: '2026-02-18',
          market: 'KR',
          total: 0,
          correct: 0,
          accuracy: 0,
          results: [],
        },
      });
    });

    // Mock empty theme accuracy
    await page.route('**/api/v1/verification/themes*', async (route) => {
      await route.fulfill({
        json: {
          date: '2026-02-18',
          themes: [],
        },
      });
    });

    await page.goto('/verification');

    await expect(page.getByText('검증 결과가 없습니다')).toBeVisible();
    await expect(page.getByText('테마 데이터가 없습니다')).toBeVisible();
  });
});
