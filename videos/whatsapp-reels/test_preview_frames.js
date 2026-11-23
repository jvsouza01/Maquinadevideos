const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const puppeteer = require('puppeteer-core');

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
  throw new Error('Chrome executable not found.');
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: resolveChromePath(),
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const fileUrl = 'file://' + path.resolve(__dirname, 'index.html').replace(/\\/g, '/');
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });

  const sampleDir = fs.mkdtempSync(path.join(os.tmpdir(), 'wa-reels-test-'));

  try {
    const cases = [
      {
        t: 0.8,
        check: (s) => {
          assert.strictEqual(s.visibleMessages, 0, 't=0.8 should have 0 sent messages yet');
          assert.ok(s.inputText.length > 0, 't=0.8 should show active client typing text');
          assert.strictEqual(s.cursorVisible, true, 't=0.8 cursor should be visible');
          assert.strictEqual(s.outroVisible, false, 't=0.8 outro must be hidden');
        }
      },
      {
        t: 2.2,
        check: (s) => {
          assert.strictEqual(s.visibleMessages, 1, 't=2.2 should show first client message');
          assert.strictEqual(s.vrTyping, true, 't=2.2 should show VR typing indicator');
          assert.strictEqual(s.contactStatus, 'digitando...', 't=2.2 status should be digitando...');
        }
      },
      {
        t: 15.0,
        check: (s) => {
          assert.strictEqual(s.visibleMessages, 6, 't=15.0 should show 6 messages');
          assert.ok(s.inputText.length > 0, 't=15.0 client should be typing msg 7');
        }
      },
      {
        t: 29.9,
        check: (s) => {
          assert.strictEqual(s.visibleMessages, 14, 't=29.9 should show all 14 messages');
          assert.ok(s.scrollOffset > 0, 't=29.9 viewport should scroll downward smoothly');
        }
      },
      {
        t: 31.5,
        check: (s) => {
          assert.strictEqual(s.outroVisible, true, 't=31.5 outro should be visible');
          assert.strictEqual(s.outroImg1Visible, true, 't=31.5 outro-img-1 should be visible');
          assert.strictEqual(s.outroImg2Visible, false, 't=31.5 outro-img-2 should be hidden');
        }
      },
      {
        t: 34.5,
        check: (s) => {
          assert.strictEqual(s.outroVisible, true, 't=34.5 outro should be visible');
          assert.strictEqual(s.outroImg1Visible, false, 't=34.5 outro-img-1 should be hidden');
          assert.strictEqual(s.outroImg2Visible, true, 't=34.5 outro-img-2 should be visible');
        }
      }
    ];

    for (const c of cases) {
      const stateA = await page.evaluate((currTime) => {
        window.chatTimeline.renderFrame(currTime);
        return window.chatTimeline.getState();
      }, c.t);
      // Verify deterministic seek: re-seeking to same timestamp yields identical state
      const stateB = await page.evaluate((currTime) => {
        window.chatTimeline.renderFrame(currTime);
        return window.chatTimeline.getState();
      }, c.t);
      assert.deepStrictEqual(stateA, stateB, `Non-deterministic state at t=${c.t}`);
      c.check(stateA);

      const pngPath = path.join(sampleDir, `test_frame_${c.t.toFixed(1)}s.png`);
      await page.screenshot({ path: pngPath, type: 'png' });
      const stat = fs.statSync(pngPath);
      assert.ok(stat.size > 10000, `Rendered PNG too small at t=${c.t}: ${stat.size} bytes`);
      console.log(`PASS t=${c.t.toFixed(1)}s (msgs=${stateA.visibleMessages}, scroll=${stateA.scrollOffset}px, ${stat.size}B)`);
    }

    // Verify HyperFrames-compatible seek contract
    const hfOk = await page.evaluate(() => {
      const tl = window.__timelines && window.__timelines['whatsapp-reels'];
      if (!tl) return false;
      tl.seek(2.2);
      const st = window.chatTimeline.getState();
      return st.vrTyping === true && tl.duration() === 36;
    });
    assert.strictEqual(hfOk, true, 'HyperFrames-compatible timeline contract failed');
    console.log('PASS HyperFrames-compatible deterministic timeline contract');
  } finally {
    await browser.close();
    fs.rmSync(sampleDir, { recursive: true, force: true });
  }
})();
