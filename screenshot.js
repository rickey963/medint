const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:3000/medint/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const cif = document.querySelector('h2')?.closest('div.h-\\[450px\\], div.flex.flex-col');
    const heroBoxes = Array.from(document.querySelectorAll('.lg\\:col-span-2, .lg\\:col-span-1'));
    const tileBoxes = Array.from(document.querySelectorAll('main .grid > div'));
    return {
      heroBoxes: heroBoxes.map(el => ({ cls: el.className.slice(0,40), w: el.getBoundingClientRect().width, x: el.getBoundingClientRect().x })),
      tileBoxes: tileBoxes.slice(0,3).map(el => ({ w: el.getBoundingClientRect().width, x: el.getBoundingClientRect().x })),
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await page.screenshot({ path: 'screenshot_widths.png', clip: { x: 0, y: 80, width: 1440, height: 900 } });
  await browser.close();
})();
