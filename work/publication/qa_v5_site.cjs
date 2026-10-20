const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, permissions: ['clipboard-read', 'clipboard-write'] });
    context.setDefaultTimeout(15000);
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:8769/demo/');
    await page.waitForFunction(() => [...document.querySelectorAll('video')].every(video => video.readyState >= 1), { timeout: 15000 });
    const main = await page.evaluate(() => ({ videoCount: document.querySelectorAll('video').length, videos: [...document.querySelectorAll('video')].map(video => ({ source: video.currentSrc, duration: video.duration })), link: document.querySelector('a[href="v5/"]')?.href }));
    if (main.videoCount !== 3 || main.videos[0].duration !== 148.4 || !main.link) throw Error('Video integration failed');
    await page.goto(main.link);
    const canonical = JSON.parse(fs.readFileSync(path.join(root, 'outputs/nanda-demo-v5/prompts.json'), 'utf8')).prompts;
    const shown = await page.locator('[data-prompt]').evaluateAll(nodes => nodes.map(node => ({ id: node.dataset.prompt, text: node.textContent })));
    if (JSON.stringify(shown) !== JSON.stringify(canonical.map(({ id, text }) => ({ id, text })))) throw Error('Prompt mismatch');
    await page.locator('.copy').first().click();
    if (await page.evaluate(() => navigator.clipboard.readText()) !== canonical[0].text) throw Error('Clipboard text mismatch');
    const popupPromise = page.waitForEvent('popup');
    await page.locator('.shot').first().click();
    const popup = await popupPromise;
    await popup.waitForLoadState();
    const dimensions = await popup.locator('img').evaluate(image => ({ width: image.naturalWidth, height: image.naturalHeight }));
    if (dimensions.width !== 1920 || dimensions.height !== 1080) throw Error('Full-size screenshot failed');
    if (errors.length) throw Error(JSON.stringify(errors));
    const report = { main, canonicalPromptsMatch: true, clipboardExact: true, fullSizeScreenshot: dimensions, javascriptErrors: errors };
    fs.writeFileSync(path.join(__dirname, 'v5-site-qa.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
