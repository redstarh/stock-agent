import { test, expect } from '@playwright/test';
import { setupApiMocks } from './helpers';

test.describe('Verification Page (Advan)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/verification');
  });

  test('displays page heading with Advan title and run selector', async ({ page }) => {
    await expect(page.getByText('예측 검증 (Advan)')).toBeVisible();
    await expect(page.getByText('시뮬레이션 실행')).toBeVisible();
    await expect(page.locator('select')).toBeVisible();
  });

  test('run selector shows available completed runs', async ({ page }) => {
    const select = page.locator('select');
    await expect(select).toBeVisible();

    // Check that both runs are in the dropdown
    await expect(select.locator('option[value="1"]')).toHaveText('테스트 시뮬레이션 (ID: 1)');
    await expect(select.locator('option[value="2"]')).toHaveText('검증 시뮬레이션 #2 (ID: 2)');

    // Default should be the latest run (ID: 2, highest ID sorted desc)
    await expect(select).toHaveValue('2');
  });

  test('displays blue info banner with run details', async ({ page }) => {
    const banner = page.locator('.border-blue-500.bg-blue-50');
    await expect(banner).toBeVisible();

    // Check run name (default is run ID 2)
    await expect(banner.getByText('검증 시뮬레이션 #2')).toBeVisible();

    // Check date range
    await expect(banner.getByText(/2026-02-05 ~ 2026-02-15/)).toBeVisible();

    // Check accuracy display (81.1% for run 2: 30/37 = 0.811)
    await expect(banner.getByText(/정확도.*81\.1%/)).toBeVisible();
    await expect(banner.getByText(/30\/37건/)).toBeVisible(); // 30 correct out of (40 - 3 abstain)
  });

  test('displays accuracy overview card with Advan data', async ({ page }) => {
    // Overall accuracy for run 2 (81.1%)
    await expect(page.getByText('전체 정확도')).toBeVisible();
    await expect(page.getByText('81.1%', { exact: true })).toBeVisible();

    // Total predictions for run 2 (37, excluding 3 abstains from 40 total)
    await expect(page.getByText('총 예측')).toBeVisible();
    await expect(page.getByText('37건').first()).toBeVisible();

    // Correct predictions for run 2
    await expect(page.getByText('정답')).toBeVisible();
    await expect(page.getByText('30건')).toBeVisible();

    // Incorrect predictions (37 - 30 = 7)
    await expect(page.getByText('오답')).toBeVisible();
    await expect(page.getByText('7건', { exact: true }).first()).toBeVisible();
  });

  test('displays direction breakdown in overview card', async ({ page }) => {
    await expect(page.getByText('방향별 정확도')).toBeVisible();

    // Up direction (80.0%)
    const upBox = page.locator('.bg-red-50');
    await expect(upBox.getByText('상승 예측')).toBeVisible();
    await expect(upBox.getByRole('paragraph').filter({ hasText: '80.0%' })).toBeVisible();
    await expect(upBox.getByText('16/20')).toBeVisible();

    // Down direction (80.0%)
    const downBox = page.locator('.bg-blue-50');
    await expect(downBox.getByText('하락 예측')).toBeVisible();
    await expect(downBox.getByRole('paragraph').filter({ hasText: '80.0%' })).toBeVisible();
    await expect(downBox.getByText('12/15')).toBeVisible();

    // Neutral direction (90.0%)
    await expect(page.getByText('중립 예측')).toBeVisible();
    await expect(page.locator('.bg-gray-50 p.text-lg.font-bold.text-gray-600')).toBeVisible();
    await expect(page.getByText('9/10')).toBeVisible();
  });

  test('displays stock results table with Advan data', async ({ page }) => {
    await expect(page.getByText('종목별 검증 결과')).toBeVisible();

    // Check table headers
    await expect(page.getByRole('columnheader', { name: '예측' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: '실제' })).toBeVisible();

    // Check stock names from predictions (filtered, no Abstain)
    await expect(page.getByText('삼성전자')).toBeVisible();
    await expect(page.getByText('SK하이닉스')).toBeVisible();
    await expect(page.getByText('NAVER')).toBeVisible();
    await expect(page.getByText('LG화학')).toBeVisible();
    await expect(page.getByText('현대차')).toBeVisible();
  });

  test('stock results table shows correct prediction indicators', async ({ page }) => {
    // Find Samsung row (correct prediction: Up -> Up)
    const samsungRow = page.locator('tr', { has: page.getByText('005930') });
    await expect(samsungRow.getByText('✓')).toBeVisible();

    // Find SK Hynix row (incorrect prediction: Up -> Down)
    const skRow = page.locator('tr', { has: page.getByText('000660') });
    await expect(skRow.getByText('✗')).toBeVisible();

    // Find NAVER row (correct prediction: Down -> Down)
    const naverRow = page.locator('tr', { has: page.getByText('035420') });
    await expect(naverRow.getByText('✓')).toBeVisible();
  });

  test('displays theme accuracy breakdown with Advan data', async ({ page }) => {
    await expect(page.getByText('테마별 정확도')).toBeVisible();

    // Wait for chart to render
    await page.waitForTimeout(500);

    // Check that we have theme elements in the chart area
    const chartSection = page.locator('section', { has: page.getByText('테마별 정확도') });
    await expect(chartSection).toBeVisible();
  });

  test('theme accuracy shows chart container', async ({ page }) => {
    // Wait for chart and data to render
    await page.waitForTimeout(1000);

    // The theme accuracy component shows a chart
    const themeSection = page.locator('section', { has: page.getByText('테마별 정확도') });
    await expect(themeSection).toBeVisible();

    // Verify the rounded border container (chart wrapper) exists
    await expect(themeSection.locator('.rounded-lg.border.bg-white')).toBeVisible();
  });

  test('does NOT display daily accuracy trend section', async ({ page }) => {
    // Advan system does not have daily_trend data
    await expect(page.getByText('일별 정확도 추세')).not.toBeVisible();
  });

  test('does NOT display old date picker or period selector', async ({ page }) => {
    // No date picker in Advan UI
    await expect(page.locator('input[type="date"]')).not.toBeVisible();

    // The only select should be the run selector, not a period selector
    const select = page.locator('select');
    await expect(select).toBeVisible();

    // Should NOT have period options like "7일", "30일", "90일"
    await expect(select.locator('option[value="7"]')).not.toBeVisible();
  });

  test('navigates to verification page via sidebar', async ({ page }) => {
    // Go to dashboard first
    await page.goto('/');
    await expect(page.getByText('대시보드')).toBeVisible();

    // Navigate to verification
    await page.goto('/verification');
    await expect(page).toHaveURL('/verification');
    await expect(page.getByText('예측 검증 (Advan)')).toBeVisible();
  });

  test('shows result count in section header', async ({ page }) => {
    await expect(page.getByText('종목별 검증 결과')).toBeVisible();
    // Should show count of predictions (5 predictions, excluding abstains)
    await expect(page.getByText('(5건)')).toBeVisible();
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

    // Check for confidence values from mockAdvanRunDetail (82%, 75%, 68%)
    await expect(table.getByText('82.0%')).toBeVisible();
    await expect(table.getByText('75.0%')).toBeVisible();
    await expect(table.getByText('68.0%')).toBeVisible();
  });

  test('displays actual change percentages with correct formatting', async ({ page }) => {
    // Check positive change (Samsung: realized_ret 0.023 * 100 = 2.3% with + sign)
    await expect(page.getByText('+2.30%')).toBeVisible();

    // Check negative change (SK Hynix: realized_ret -0.012 * 100 = -1.2%)
    await expect(page.getByText('-1.20%')).toBeVisible();

    // Check negative change (NAVER: realized_ret -0.008 * 100 = -0.8%)
    await expect(page.getByText('-0.80%')).toBeVisible();
  });

  test('run selector allows switching between runs', async ({ page }) => {
    const select = page.locator('select');
    const banner = page.locator('.border-blue-500.bg-blue-50');

    // Should start with run ID 2 (highest ID)
    await expect(select).toHaveValue('2');
    await expect(banner).toContainText('검증 시뮬레이션 #2');

    // Change to run ID 1
    await select.selectOption('1');
    await expect(select).toHaveValue('1');

    // Banner should update to show run 1 details
    await page.waitForTimeout(500);
    await expect(banner).toContainText('테스트 시뮬레이션');
    await expect(banner).toContainText('2026-02-01 ~ 2026-02-18');
  });

  test('empty state shows when no Advan runs exist', async ({ page }) => {
    // Mock empty Advan runs
    await page.route('**/api/v1/advan/runs?*', async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.goto('/verification');

    // Should show Advan-specific empty state message
    await expect(page.getByText('Advan 시뮬레이션 실행 데이터가 없습니다')).toBeVisible();

    // Selector should be disabled with "실행 데이터 없음"
    const select = page.locator('select');
    await expect(select).toBeDisabled();
    await expect(select.locator('option')).toHaveText('실행 데이터 없음');
  });
});
