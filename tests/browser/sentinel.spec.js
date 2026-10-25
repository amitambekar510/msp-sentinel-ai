const { test, expect } = require('@playwright/test');
const token = tenant => `synthetic-tenant-${tenant}-token-000000000000`;

test('dashboard renders existing intelligence and investigator without errors', async ({ page }, testInfo) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#risk')).toHaveText('35');
  await expect(page.locator('#brief')).toContainText('1 critical and 1 high');
  await expect(page.locator('#tenants .row')).toHaveCount(3);
  await expect(page.locator('#signals .signal')).toHaveCount(3);
  await expect(page.locator('#exposure .exposure-row')).toHaveCount(3);
  await expect(page.locator('#watchlist .signal')).toHaveCount(2);
  await expect(page.locator('#timeline .timeline-item')).toHaveCount(3);
  await expect(page.locator('#map .dot')).toHaveCount(3);
  await expect(page.locator('#graph')).toContainText('relationships');
  await page.locator('#indicator').fill('C2 infrastructure');
  await page.getByRole('button', { name: 'INVESTIGATE' }).click();
  await expect(page.locator('#investigation')).toContainText('Matches: 1');
  await page.locator('#indicator').fill('no-such-indicator');
  await page.getByRole('button', { name: 'INVESTIGATE' }).click();
  await expect(page.locator('#investigation')).toContainText('Matches: 0');
  await page.screenshot({ path: testInfo.outputPath('dashboard.png'), fullPage: true });
  expect(errors).toEqual([]);
});

test('browser tenant requests enforce credentials and preserve public boundaries', async ({ page }) => {
  await page.goto('/');
  const results = await page.evaluate(async ({ a, b }) => {
    const get = async (path, bearer) => {
      const r = await fetch(path, { headers: bearer ? { Authorization: `Bearer ${bearer}` } : {} });
      return { status: r.status, cache: r.headers.get('Cache-Control'), text: await r.text() };
    };
    return Promise.all([
      get('/api/tenants/a/wazuh'),
      get('/api/tenants/b/wazuh', a),
      get('/api/tenants/a/wazuh', a),
      get('/api/tenants/b/wazuh', b),
      get('/api/tenants/unknown/wazuh', a),
      get('/api/snapshot', a),
      get('/api/exposure', a),
      get('/api/investigate/Private', a),
    ]);
  }, { a: token('a'), b: token('b') });
  expect(results.map(r => r.status)).toEqual([401, 403, 200, 200, 403, 200, 200, 200]);
  for (const r of results.slice(0, 5)) expect(r.cache).toBe('no-store');
  expect(JSON.parse(results[2].text).alerts.map(a => a.agent_id)).toEqual(['001']);
  expect(JSON.parse(results[3].text).alerts.map(a => a.agent_id)).toEqual(['002']);
  for (const r of results) expect(r.text).not.toContain('PRIVATE RAW LOG');
  for (const r of results.slice(5)) expect(r.text).not.toContain('Private synthetic alert');
  await expect(page.locator('body')).not.toContainText('Private synthetic alert');
  const event = await page.evaluate(() => new Promise((resolve, reject) => {
    const stream = new EventSource('/api/stream');
    const timer = setTimeout(() => { stream.close(); reject(Error('SSE timed out')); }, 10000);
    stream.onmessage = e => { clearTimeout(timer); stream.close(); resolve(JSON.parse(e.data)); };
    stream.onerror = () => { clearTimeout(timer); stream.close(); reject(Error('SSE failed')); };
  }));
  expect(event.tenants).toHaveLength(3);
  expect(JSON.stringify(event)).not.toContain('Private synthetic alert');
});

test('dashboard reports refresh failure', async ({ page }) => {
  await page.route('**/api/snapshot', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  await page.goto('/');
  await expect(page.locator('#brief')).toContainText('Unable to refresh');
});
