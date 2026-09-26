// sweets/index.html をフレーム単位で書き出し、MP4 に合成する
//   node tools/render_sweets.mjs                  → sweets/sweets_sparkle.mp4
//   node tools/render_sweets.mjs --stills 0.3,2.4 → 指定秒のスチルだけ書き出し（確認用）
//   node tools/render_sweets.mjs --src pudding.webp --name pudding_sparkle --grade 'sat=0.15&bloom=0.5&warm=0.3&bright=0.4'
//     → 別の写真で書き出し（--grade で色補正の強さを調整）
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const FPS = 30;
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const src = opt('--src', 'sweets.webp');
const name = opt('--name', 'sweets_sparkle');
const grade = opt('--grade', '');
const outDir = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(root, 'sweets');

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(path.join(root, 'sweets/index.html')).href + `?render=1&src=${encodeURIComponent(src)}${grade ? '&' + grade : ''}`);
await page.waitForFunction(() => window.READY === true);
const stage = page.locator('#stage');
const grab = (t, file, type = 'png') => page.evaluate((t) => window.render(t), t)
  .then(() => stage.screenshot({ path: file, type, ...(type === 'jpeg' ? { quality: 94 } : {}) }));

if (stillsArg) {
  for (const s of stillsArg.split(',').map(Number)) {
    const file = path.join(outDir, `still_${String(s).replace('.', '_')}.png`);
    await grab(s, file);
    console.log('still', file);
  }
  await browser.close();
  process.exit(0);
}

const dur = await page.evaluate(() => window.DURATION);
const frames = fs.mkdtempSync(path.join(os.tmpdir(), 'sweets-frames-'));
const total = Math.round(dur * FPS);
for (let i = 0; i < total; i++) {
  await grab(i / FPS, path.join(frames, `f${String(i).padStart(4, '0')}.jpg`), 'jpeg');
  if (i % 30 === 0) console.log(`frame ${i}/${total}`);
}
await browser.close();

const ffmpeg = execFileSync('python3', ['-c', 'import imageio_ffmpeg as f;print(f.get_ffmpeg_exe())']).toString().trim();
const out = path.join(root, `sweets/${name}.mp4`);
execFileSync(ffmpeg, ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, 'f%04d.jpg'),
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', out], { stdio: 'inherit' });
fs.rmSync(frames, { recursive: true, force: true });
console.log('wrote', out);
