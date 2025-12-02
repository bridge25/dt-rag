import { chromium } from '@playwright/test';
import { mkdir } from 'fs/promises';
import { existsSync } from 'fs';

const BASE_URL = 'http://localhost:3001';
const SCREENSHOT_DIR = './screenshots';

const pages = [
  { name: '01-dashboard', path: '/' },
  { name: '02-taxonomy', path: '/taxonomy' },
  { name: '03-agents', path: '/agents' },
  { name: '04-chat', path: '/chat' },
  { name: '05-connect', path: '/connect' },
  { name: '06-search', path: '/search' },
  { name: '07-research', path: '/research' },
  { name: '08-documents', path: '/documents' },
  { name: '09-monitoring', path: '/monitoring' },
  { name: '10-taxonomy-builder', path: '/taxonomy-builder' },
];

async function takeScreenshots() {
  if (!existsSync(SCREENSHOT_DIR)) {
    await mkdir(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--font-render-hinting=none']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2, // Retina quality
    colorScheme: 'dark', // Enable dark mode
    locale: 'en-US',
  });

  const page = await context.newPage();

  for (const { name, path } of pages) {
    console.log(`📸 Capturing ${name}...`);
    try {
      await page.goto(`${BASE_URL}${path}`, {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      // Set dark mode class on html element
      await page.evaluate(() => {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      });

      // Wait for styles to apply
      await page.waitForTimeout(2000);

      // Disable animations for stable screenshots
      await page.addStyleTag({
        content: `
          *, *::before, *::after {
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-duration: 0s !important;
            transition-delay: 0s !important;
          }
        `
      });

      await page.waitForTimeout(500);

      await page.screenshot({
        path: `${SCREENSHOT_DIR}/${name}.png`,
        fullPage: false,
        animations: 'disabled',
      });

      console.log(`   ✅ ${name}.png saved`);
    } catch (error) {
      console.error(`   ❌ Failed to capture ${name}: ${error.message}`);
    }
  }

  await browser.close();
  console.log('\n🎉 All screenshots completed!');
}

takeScreenshots().catch(console.error);
