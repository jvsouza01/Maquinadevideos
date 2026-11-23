const { spawn, execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');

const DURATION = 36.0;
const FPS = 30;
const TOTAL_FRAMES = Math.round(DURATION * FPS); // 1080 frames
const WIDTH = 1080;
const HEIGHT = 1920;

function resolveChromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium'
  ].filter(Boolean);
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error(`Chrome executable not found. Set CHROME_PATH env var. Checked: ${candidates.join(', ')}`);
}

async function main() {
  console.log('=== [1/4] Building Audio ===');
  const buildAudioScript = path.join(__dirname, 'build_audio.py');
  execFileSync('python', [buildAudioScript], { stdio: 'inherit' });

  const finalAudioPath = path.join(__dirname, 'final_audio.wav');
  if (!fs.existsSync(finalAudioPath)) {
    throw new Error('Audio file was not generated!');
  }

  console.log('=== [2/4] Initializing Headless Chrome ===');
  const chromePath = resolveChromePath();
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--font-render-hinting=none',
      '--enable-font-antialiasing'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });

  const htmlUrl = 'file://' + path.resolve(__dirname, 'index.html').replace(/\\/g, '/');
  await page.goto(htmlUrl, { waitUntil: 'networkidle0' });

  console.log(`=== [3/4] Rendering ${TOTAL_FRAMES} lossless PNG frames (${DURATION}s @ ${FPS}fps) ===`);
  const tempVideoPath = path.join(__dirname, 'temp_video.mp4');

  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', FPS.toString(),
    '-i', '-',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    tempVideoPath
  ]);

  let stderrTail = '';
  ffmpeg.stderr.on('data', (chunk) => {
    stderrTail = (stderrTail + chunk.toString()).slice(-4000);
  });

  const ffmpegExit = new Promise((resolve, reject) => {
    ffmpeg.on('error', reject);
    ffmpeg.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`FFmpeg exited with code ${code}:\n${stderrTail}`));
    });
  });

  const startTime = Date.now();

  try {
    for (let frame = 0; frame < TOTAL_FRAMES; frame++) {
      const t = frame / FPS;

      await page.evaluate((currTime) => {
        window.chatTimeline.renderFrame(currTime);
      }, t);

      const buf = await page.screenshot({ type: 'png' });

      const canWrite = ffmpeg.stdin.write(buf);
      if (!canWrite) {
        await new Promise((resolve) => ffmpeg.stdin.once('drain', resolve));
      }

      if (frame % 90 === 0 || frame === TOTAL_FRAMES - 1) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        const percent = ((frame / TOTAL_FRAMES) * 100).toFixed(1);
        console.log(`Frame ${frame}/${TOTAL_FRAMES} (${percent}%) | Time: ${t.toFixed(2)}s | Elapsed: ${elapsed}s`);
      }
    }
  } finally {
    ffmpeg.stdin.end();
    await browser.close();
  }

  await ffmpegExit;

  console.log('=== [4/4] Muxing Audio & Finalizing MP4 ===');
  const finalVideoPath = path.join(__dirname, 'reels_black_friday_vistarumo.mp4');

  execFileSync('ffmpeg', [
    '-y',
    '-i', tempVideoPath,
    '-i', finalAudioPath,
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    finalVideoPath
  ], { stdio: 'inherit' });

  if (fs.existsSync(tempVideoPath)) {
    fs.unlinkSync(tempVideoPath);
  }

  console.log('=== RENDER COMPLETE ===');
  console.log(`Output: ${finalVideoPath}`);

  const probeOut = execFileSync('ffprobe', [
    '-v', 'error', '-show_format', '-show_streams', finalVideoPath
  ]).toString();
  console.log('Probe summary:');
  const durationMatch = probeOut.match(/duration=([0-9.]+)/);
  const widthMatch = probeOut.match(/width=([0-9]+)/);
  const heightMatch = probeOut.match(/height=([0-9]+)/);
  const fpsMatch = probeOut.match(/r_frame_rate=([0-9/]+)/);
  console.log(`Resolution: ${widthMatch ? widthMatch[1] : '?'}x${heightMatch ? heightMatch[1] : '?'}`);
  console.log(`Duration: ${durationMatch ? durationMatch[1] : '?'}s`);
  console.log(`FPS: ${fpsMatch ? fpsMatch[1] : '?'}`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
