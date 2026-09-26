// video/index.html をフレーム単位で書き出し、MP4 に合成する
//   node tools/render_video.mjs                 → video/pacchin_teaser.mp4
//   node tools/render_video.mjs --stills 1,4,8  → 指定秒のスチルだけ書き出し（確認用）
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
const outDir = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(root, 'video');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(path.join(root, 'video/index.html')).href + '?render=1');
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);
const stage = page.locator('#stage');

if (stillsArg) {
  for (const s of stillsArg.split(',').map(Number)) {
    await page.evaluate((t) => window.render(t), s);
    const file = path.join(outDir, `still_${String(s).replace('.', '_')}.png`);
    await stage.screenshot({ path: file });
    console.log('still', file);
  }
  await browser.close();
  process.exit(0);
}

const dur = await page.evaluate(() => window.DURATION);
const frames = fs.mkdtempSync(path.join(os.tmpdir(), 'pacchin-frames-'));
const total = Math.round(dur * FPS);
for (let i = 0; i < total; i++) {
  await page.evaluate((t) => window.render(t), i / FPS);
  await stage.screenshot({ path: path.join(frames, `f${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 92 });
  if (i % 60 === 0) console.log(`frame ${i}/${total}`);
}
await browser.close();

const ffmpeg = execFileSync('python3', ['-c', 'import imageio_ffmpeg as f;print(f.get_ffmpeg_exe())']).toString().trim();
const wav = path.join(frames, 'sfx.wav');
execFileSync('python3', [path.join(root, 'tools/sfx.py'), wav, String(dur)], { stdio: 'inherit' });
const out = path.join(root, 'video/pacchin_teaser.mp4');
execFileSync(ffmpeg, ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, 'f%04d.jpg'),
  '-i', wav, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow',
  '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
fs.rmSync(frames, { recursive: true, force: true });
console.log('wrote', out);
