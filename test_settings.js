import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  await page.goto('http://localhost:5899/');
  await page.waitForLoadState('networkidle');
  
  console.log('Clicking settings...');
  await page.click('text="Settings"');
  
  await page.waitForTimeout(2000);
  
  const content = await page.content();
  if (content.includes('Local API access')) {
    console.log('Settings page loaded successfully!');
  } else {
    console.log('Settings page did NOT load. Body:', await page.innerHTML('body'));
  }
  
  await browser.close();
})();
