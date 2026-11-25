import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
test('navigation, filters, traceability and screenshots', async ({page})=>{
  await page.setViewportSize({width:1536,height:1024});
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  const shots=path.resolve('docs/screenshots');fs.mkdirSync(shots,{recursive:true});
  await page.screenshot({path:path.join(shots,'overview.png'),fullPage:true});
  await page.getByRole('button',{name:'Telemetry'}).click();await expect(page.getByRole('heading',{name:'Telemetry Explorer'})).toBeVisible();await page.getByRole('button',{name:'Export CSV'}).click();await page.screenshot({path:path.join(shots,'telemetry.png'),fullPage:true});
  await page.getByRole('button',{name:/Anomalies/}).click();await expect(page.getByRole('heading',{name:/Anomaly Events/})).toBeVisible();await page.getByRole('button',{name:'Copy JSON'}).click();await page.screenshot({path:path.join(shots,'anomalies.png'),fullPage:true});
  await page.getByRole('button',{name:'Logs'}).click();await expect(page.getByRole('heading',{name:'Event Log'})).toBeVisible();await page.screenshot({path:path.join(shots,'logs.png'),fullPage:true});
});
