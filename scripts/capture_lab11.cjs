// Captures actual rendered local pages; does not manufacture GitHub/Obsidian evidence.
const { chromium } = require(process.env.LAB11_PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const out = path.resolve('Lab11/evidence/screenshots');fs.mkdirSync(out,{recursive:true});
  await page.goto('http://127.0.0.1:8001/',{waitUntil:'networkidle'});
  await page.screenshot({path:path.join(out,'mkdocs-home.png'),fullPage:true});
  await page.goto('http://127.0.0.1:8001/api/',{waitUntil:'networkidle'});
  await page.screenshot({path:path.join(out,'mkdocs-api.png'),fullPage:true});
  await page.goto('http://127.0.0.1:8000/contract-docs',{waitUntil:'networkidle'});
  const operation=page.locator('.opblock-get').filter({hasText:'/api/v1/shipping/policy'});
  await operation.locator('.opblock-summary').click();
  await operation.getByRole('button',{name:'Try it out'}).click();
  await operation.getByRole('button',{name:'Execute',exact:true}).click();
  await operation.locator('.live-responses-table').waitFor();
  await page.screenshot({path:path.join(out,'swagger-try-it-out.png'),fullPage:true});
  await browser.close();
})();
