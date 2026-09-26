// SVG → PNG 書き出し（Chromium で描画するのでフォントも正しく反映される）
//   node tools/render.mjs design/package_grape.svg out.png [scale]
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const jobs = [];
for (let i = 2; i < process.argv.length; i += 3) {
  jobs.push([process.argv[i], process.argv[i + 1], Number(process.argv[i + 2] || 2)]);
}

const browser = await chromium.launch();
for (const [src, out, scale] of jobs) {
  const page = await browser.newPage({ deviceScaleFactor: scale });
  await page.goto(pathToFileURL(path.resolve(src)).href);
  await page.evaluate(() => document.fonts.ready);
  const size = await page.evaluate(() => {
    const s = document.documentElement;
    const vb = s.viewBox.baseVal;
    s.setAttribute('width', vb.width);
    s.setAttribute('height', vb.height);
    return { width: Math.ceil(vb.width), height: Math.ceil(vb.height) };
  });
  await page.setViewportSize(size);
  await page.waitForTimeout(150);
  await page.screenshot({ path: out, omitBackground: true });
  console.log('rendered', out);
  await page.close();
}
await browser.close();
