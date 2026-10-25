/** Rebuild README media using the real application and synthetic browser fixture. */
const { chromium } = require('playwright');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const python = process.env.PYTHON || 'python';
const baseURL = 'http://127.0.0.1:8766';
const C = { bg: '#07131d', panel: '#0c2130', edge: '#214052', text: '#edf7fc', muted: '#aac2d0', mint: '#58e6c2', cyan: '#3bd7ef', amber: '#f1c879' };
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));
const text = (x, y, value, size = 22, fill = C.text, weight = 400) => `<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}">${esc(value)}</text>`;
const rect = (x, y, w, h, fill = C.panel, radius = 16, stroke = C.edge) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${radius}" fill="${fill}" stroke="${stroke}"/>`;
const svg = (height, title, description, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="${height}" viewBox="0 0 1400 ${height}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(description)}</desc><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#07131d"/><stop offset="1" stop-color="#103244"/></linearGradient><pattern id="grid" width="44" height="44" patternUnits="userSpaceOnUse"><path d="M44 0H0V44" fill="none" stroke="#79bed3" stroke-opacity=".055"/></pattern><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6" fill="none" stroke="${C.mint}" stroke-width="1.4"/></marker></defs><rect width="1400" height="${height}" fill="url(#bg)"/><rect width="1400" height="${height}" fill="url(#grid)"/><g font-family="Arial, Helvetica, sans-serif">${body}</g></svg>\n`;
const arrow = (x1, y1, x2, y2) => `<path d="M${x1} ${y1}L${x2} ${y2}" stroke="${C.mint}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;

function hero() {
  let s = rect(56, 45, 66, 5, C.mint, 2, C.mint);
  s += text(56, 88, 'OPEN-SOURCE SOC SITUATION ROOM', 19, C.mint, 700);
  s += text(52, 192, 'MSP Sentinel AI', 78, C.text, 700);
  s += text(52, 298, '3.1', 108, C.mint, 700);
  s += text(56, 354, 'Public intelligence. Private telemetry.', 31, C.text, 700);
  s += text(56, 394, 'A clearer boundary for the MSP analyst.', 26, C.muted);
  ['CTI FUSION', 'WAZUH READ API', 'TENANT SAFEGUARDS'].forEach((label, i) => {
    const widths = [159, 205, 248];
    const x = [56, 229, 448][i];
    s += rect(x, 429, widths[i], 42, '#102d3c', 10) + text(x + 16, 456, label, 16, C.cyan, 700);
  });
  s += rect(890, 104, 454, 367, '#0a1d2a', 20);
  s += text(918, 147, 'WAZUH CONNECTOR', 20, C.cyan, 700);
  s += rect(918, 171, 226, 31, '#173d37', 8, '#326b5c') + text(931, 193, 'SYNTHETIC VERIFICATION', 14, C.mint, 700);
  s += text(918, 246, 'Read-only alert search', 28, C.text, 700);
  [['Tenant-bound token', 'AUTH'], ['Explicit agent assignment', 'SCOPE'], ['TLS + response validation', 'CHECK']].forEach(([label, tag], i) => {
    const y = 290 + i * 55;
    s += rect(918, y - 23, 62, 28, '#102f3e', 6) + text(928, y - 3, tag, 12, C.mint, 700) + text(993, y, label, 20, C.muted);
  });
  s += `<path d="M56 505H1344" stroke="${C.edge}"/>` + text(56, 541, 'SYNTHETIC DEMO  /  PRODUCTION TENANT ISOLATION NOT VERIFIED', 18, C.amber, 700);
  return svg(570, 'MSP Sentinel AI 3.1', 'Public CTI fusion, a read-only Wazuh indexer connector and verified synthetic safeguards. Production tenant isolation remains unverified.', s);
}

function architecture() {
  let s = text(48, 58, 'MSP SENTINEL AI 3.1', 22, C.mint, 700) + text(48, 108, 'Two paths. An explicit data boundary.', 39, C.text, 700);
  function lane(y, name, caption, items, color) {
    let out = rect(48, y, 1304, 210, '#091c29', 18);
    out += text(72, y + 35, name, 17, color, 700) + text(72, y + 66, caption, 18, C.muted);
    items.forEach(([title, line1, line2], i) => {
      const x = 72 + i * 320;
      out += rect(x, y + 88, 290, 98, '#102a3a', 12);
      out += text(x + 18, y + 119, title, 22, C.text, 700) + text(x + 18, y + 147, line1, 17, C.muted) + text(x + 18, y + 172, line2, 17, C.muted);
      if (i < 3) out += arrow(x + 294, y + 137, x + 315, y + 137);
    });
    return out;
  }
  s += lane(142, 'PUBLIC INTELLIGENCE + SYNTHETIC TENANTS', 'Existing dashboard functionality is preserved.', [
    ['Public CTI', 'CISA KEV · NVD', 'URLhaus · Feodo Tracker'], ['Fusion + resilience', 'Normalize · retry · fallback', 'Synthetic tenant context'], ['Public dashboard + API', 'Snapshot · exposure · SSE', 'Investigator · graph · timeline'], ['Optional local AI', 'Grounded situation brief', 'Public / demo inputs only'],
  ], C.cyan);
  s += text(72, 393, 'NO PRIVATE WAZUH DATA IN PUBLIC SNAPSHOTS, STREAMS OR AI', 18, C.amber, 700);
  s += lane(420, 'PRIVATE TELEMETRY · AUTHENTICATED TENANT API', 'A tenant token is checked before any upstream search. Connector is disabled by default.', [
    ['Wazuh indexer', 'Search-only credentials', 'HTTPS + trusted CA'], ['Scope + validation', 'Explicit agent allowlist', '24 hours · up to 100 alerts'], ['Tenant-bound API', 'Token must match tenant', 'No-store · sanitized errors'], ['Authorized caller', 'Normalized recent alerts', 'No raw logs or shared cache'],
  ], C.mint);
  s += text(48, 675, 'Synthetic checks: Python + Chromium / Firefox / WebKit', 20, C.mint, 700);
  s += text(48, 710, 'Production isolation, live upstream permissions and deployment controls still require verification.', 20, C.amber);
  return svg(742, 'MSP Sentinel AI 3.1 architecture', 'Separate public CTI and private Wazuh paths. Private telemetry is scoped to an authenticated tenant API and never enters the public snapshot, stream or optional AI.', s);
}

async function main() {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'sentinel-visuals-'));
  const assets = path.join(root, 'assets');
  await fs.writeFile(path.join(assets, 'msp-v3-hero.svg'), hero());
  await fs.writeFile(path.join(assets, 'msp-v3-architecture.svg'), architecture());
  let server;
  let browser;
  const jobs = [];
  try {
    // Refuse to capture an unrelated server already occupying the fixture port.
    let occupied = false;
    try { await fetch(`${baseURL}/api/health`); occupied = true; } catch {}
    if (occupied) throw Error('Port 8766 is already occupied; stop that server before rendering.');
    server = spawn(python, ['-m', 'uvicorn', 'browser_fixture:app', '--app-dir', 'tests', '--host', '127.0.0.1', '--port', '8766'], { cwd: root, stdio: ['ignore', 'ignore', 'inherit'] });
    let ready = false;
    for (let i = 0; i < 60; i++) {
      if (server.exitCode !== null) throw Error('Synthetic fixture stopped before becoming ready');
      try { const r = await fetch(`${baseURL}/api/health`); if (r.ok) { ready = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    if (!ready) throw Error('Synthetic fixture did not become ready');
    browser = await chromium.launch();
    const graphic = await browser.newPage({ viewport: { width: 1400, height: 570 }, deviceScaleFactor: 1 });
    for (const [stem, height] of [['msp-v3-hero', 570], ['msp-v3-architecture', 742]]) {
      await graphic.setViewportSize({ width: 1400, height });
      await graphic.setContent(`<body style="margin:0">${await fs.readFile(path.join(assets, `${stem}.svg`), 'utf8')}</body>`);
      await graphic.screenshot({ path: path.join(assets, `${stem}.png`) });
    }
    const page = await browser.newPage({ viewport: { width: 1200, height: 840 }, deviceScaleFactor: 1 });
    await page.goto(baseURL);
    await page.waitForFunction(() => document.querySelector('#risk').textContent === '35');
    await page.addStyleTag({ content: '* { animation:none!important; transition:none!important } html { scroll-behavior:auto!important } body { padding-bottom:90px }' });
    await page.evaluate(() => {
      const label = document.createElement('div');
      label.id = 'capture-label';
      label.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#07131df5;border-top:2px solid #58e6c2;padding:16px 26px;color:#edf7fc;font:600 18px Arial;line-height:1.5';
      document.body.append(label);
    });
    async function caption(title, detail) {
      await page.locator('#capture-label').evaluate((el, { title, detail }) => {
        el.replaceChildren();
        const top = document.createElement('div'); top.textContent = `MSP SENTINEL AI 3.1  /  ${title}`;
        const bottom = document.createElement('div'); bottom.textContent = `SYNTHETIC DEMO · ${detail}`;
        bottom.style.cssText = 'color:#aac2d0;font:14px Arial;margin-top:3px';
        el.append(top, bottom);
      }, { title, detail });
    }
    async function capture(name, steps) {
      const dir = path.join(tmp, name); await fs.mkdir(dir);
      const files = []; const durations = [];
      for (let i = 0; i < steps.length; i++) {
        const [selector, title, detail, action] = steps[i];
        if (action) await action();
        const target = await page.locator(selector).first().evaluate(el => window.scrollY + el.getBoundingClientRect().top - 26);
        await page.evaluate(y => window.scrollTo(0, Math.max(0, y)), target);
        await caption(title, detail);
        const file = path.join(dir, `${i}.png`);
        await page.screenshot({ path: file });
        files.push(file); durations.push(1900);
      }
      jobs.push({ output: path.join(assets, `${name}.gif`), files, durations });
    }
    const investigate = async () => {
      await page.locator('#indicator').fill('C2 infrastructure');
      await page.locator('#investigate-form button').click();
      await page.waitForFunction(() => document.querySelector('#investigation').textContent.includes('Matches: 1'));
    };
    await capture('msp-sentinel-ai-demo', [
      ['header', 'THE SITUATION ROOM', 'Public intelligence + fictional MSP tenants'],
      ['.grid', 'SOURCE-AWARE INTELLIGENCE', 'Synthetic feeds exercise the real dashboard'],
      ['.lower', 'TENANT HEALTH + PRIORITY SIGNALS', 'Illustrative operations data; no customer telemetry'],
      ['.v2-grid', 'EXPLAINABLE EXPOSURE', 'Estimates provide context, not proof of compromise'],
      ['.investigator', 'INVESTIGATE THE EVIDENCE', 'A real search against the synthetic snapshot', investigate],
      ['header', 'READY FOR A VERIFIED PILOT', 'Production tenant isolation remains unverified'],
    ]);
    await page.evaluate(() => window.scrollTo(0, 0));
    await caption('THE SITUATION ROOM', 'Public intelligence + fictional MSP tenants');
    await page.locator('#capture-label').evaluate(el => { el.style.position = 'static'; document.body.prepend(el); });
    await page.screenshot({ path: path.join(assets, 'msp-sentinel-dashboard.png'), fullPage: true });
    await page.locator('#capture-label').evaluate(el => { el.style.position = 'fixed'; document.body.append(el); });
    await capture('msp-sentinel-cti-fusion', [
      ['.grid', '01 / PUBLIC CTI CONTEXT', 'CISA KEV · NVD · URLhaus · Feodo supported; synthetic capture'],
      ['#signals', '02 / NORMALIZED SIGNALS', 'Severity and source stay visible to the analyst'],
      ['#watchlist', '03 / PRIORITIZE + CORRELATE', 'Watchlist, timeline and graph retain evidence context'],
      ['.grid', '04 / SOURCE HEALTH', 'Fallback remains explicit when upstream sources fail'],
    ]);
    await capture('msp-sentinel-multi-tenant', [
      ['.lower', '01 / SYNTHETIC MSP TENANTS', 'Fictional client health and operational metrics'],
      ['#exposure', '02 / EXPOSURE ESTIMATES', 'Confidence and prioritization are demonstration context'],
      ['#graph', '03 / KEEP THE BOUNDARY CLEAR', 'Private Wazuh reads use a separate authenticated API'],
      ['.lower', '04 / VERIFY BEFORE PRODUCTION', 'Synthetic checks do not establish production isolation'],
    ]);
    await capture('msp-sentinel-ai-analyst', [
      ['.grid', '01 / GROUNDED SITUATION BRIEF', 'Deterministic briefing shown; local Ollama is optional'],
      ['#watchlist', '02 / EVIDENCE BEFORE ESCALATION', 'Prioritize signals and preserve source context'],
      ['.investigator', '03 / INVESTIGATE + CORROBORATE', 'Search the public / demo snapshot', investigate],
      ['.grid', '04 / PRIVATE DATA STAYS SEPARATE', 'Wazuh tenant alerts are never sent to this AI brief'],
    ]);
    const a = 'synthetic-tenant-a-token-000000000000';
    const allowed = await page.request.get(`${baseURL}/api/tenants/a/wazuh?limit=1`, { headers: { Authorization: `Bearer ${a}` } });
    const denied = await page.request.get(`${baseURL}/api/tenants/b/wazuh`, { headers: { Authorization: `Bearer ${a}` } });
    const result = await allowed.json();
    if (allowed.status() !== 200 || result.alerts[0].agent_id !== '001' || denied.status() !== 403) throw Error('Synthetic tenant contract did not pass');
    const deniedBody = await denied.json();
    const slides = [
      ['01', 'A tenant-scoped request', 'Only an operator-assigned token can access this tenant.', 'GET /api/tenants/a/wazuh?limit=1\nAuthorization: Bearer [REDACTED]', 'TOKEN CHECK → FIXED AGENT SCOPE → READ-ONLY SEARCH', C.cyan],
      ['02', 'A bounded alert response', 'Actual response captured from the synthetic integration fixture.', JSON.stringify({ tenant_id: result.tenant_id, read_only: result.read_only, window_hours: result.window_hours, limit: result.limit, alerts: result.alerts.map(({ agent_id, rule_id, severity }) => ({ agent_id, rule_id, severity })) }, null, 2), 'HTTP 200 · TENANT A · AGENT 001', C.mint],
      ['03', 'Cross-tenant access is denied', 'The same tenant A token cannot read tenant B.', 'GET /api/tenants/b/wazuh\nAuthorization: Bearer [TENANT A TOKEN]\n\nHTTP 403\n' + JSON.stringify(deniedBody, null, 2), 'DENIED BEFORE ANY UPSTREAM REQUEST', C.amber],
      ['04', 'An explicit public / private boundary', 'Tenant telemetry remains separate from the existing situation room.', 'PRIVATE WAZUH ALERTS\n  → authenticated tenant API only\n\nPUBLIC SNAPSHOT · SSE · AI BRIEF\n  → public intelligence + synthetic demo tenants', 'SYNTHETIC SAFEGUARDS VERIFIED · PRODUCTION ISOLATION UNVERIFIED', C.cyan],
    ];
    const files = [];
    for (const [i, title, subtitle, code, foot, accent] of slides) {
      await graphic.setViewportSize({ width: 1200, height: 800 });
      await graphic.setContent(`<style>*{box-sizing:border-box}body{margin:0;background:${C.bg};color:${C.text};font:20px Arial;padding:44px}header{display:flex;justify-content:space-between;color:${C.mint};font-size:17px;font-weight:700;letter-spacing:2px}h1{font-size:42px;margin:42px 0 12px}p{color:${C.muted};font-size:21px}pre{background:${C.panel};border:1px solid ${C.edge};border-left:4px solid ${accent};border-radius:14px;padding:24px;font:21px/1.45 monospace;min-height:340px;margin-top:28px;white-space:pre-wrap}footer{color:${accent};font-size:16px;font-weight:700;margin:22px 0}small{color:${C.muted};font-size:15px}</style><header><span>MSP SENTINEL AI 3.1</span><span>WAZUH / ${i}</span></header><h1>${esc(title)}</h1><p>${esc(subtitle)}</p><pre>${esc(code)}</pre><footer>${esc(foot)}</footer><small>SYNTHETIC DEMO · No live customer data · Production validation still required</small>`);
      const file = path.join(tmp, `wazuh-${i}.png`);
      await graphic.screenshot({ path: file }); files.push(file);
    }
    jobs.push({ output: path.join(assets, 'msp-sentinel-wazuh.gif'), files, durations: [2200, 3000, 2600, 3000] });
    const manifest = path.join(tmp, 'manifest.json');
    await fs.writeFile(manifest, JSON.stringify(jobs));
    const encoded = spawnSync(process.env.IMAGE_PYTHON || python, [path.join(__dirname, 'encode_visuals.py'), manifest], { stdio: 'inherit' });
    if (encoded.status !== 0) throw Error('GIF encoder failed (install Pillow in the selected PYTHON environment)');
    console.log('Updated 2 SVGs, 3 PNGs and 5 GIFs from the synthetic fixture.');
  } finally {
    if (browser) await browser.close();
    if (server) {
      const exited = new Promise(resolve => server.once('exit', resolve));
      server.kill('SIGTERM');
      await exited;
    }
    await fs.rm(tmp, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
