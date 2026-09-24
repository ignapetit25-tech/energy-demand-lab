const {chromium}=require('playwright');
const path=require('path');
const assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('file://'+path.resolve(__dirname,'../dashboard/monthly-report.html'));
  assert.equal(await page.locator('#report-period').inputValue(),'2026-08-01');
  assert.match(await page.locator('#total').innerText(),/12\.432,0/);
  assert.match(await page.locator('#yoy').innerText(),/\+6,1%/);
  assert.equal(await page.locator('#sector-rows tr').count(),3);
  assert.match(await page.locator('#sector-rows').innerText(),/-21,6/);
  await page.selectOption('#report-period','2025-08-01');
  assert.match(await page.locator('#total').innerText(),/11\.718,8/);
  for(const [id,suffix] of [['export-text','.md'],['export-sectors','.csv']]){
   const pending=page.waitForEvent('download');await page.click('#'+id);const file=await pending;
   assert.ok(file.suggestedFilename().includes('2025-08')&&file.suggestedFilename().endsWith(suffix));
   const stream=await file.createReadStream();let content='';for await(const chunk of stream)content+=chunk;
   assert.ok(content.includes('2025-08')||content.includes('agosto de 2025'));
  }
  await page.selectOption('#report-period','2026-08-01');
  await page.evaluate(()=>{window.print=()=>{window.printWasCalled=true;};});
  await page.click('#print-report');assert.equal(await page.evaluate(()=>window.printWasCalled),true);
  await page.screenshot({path:path.resolve(__dirname,'../dashboard/report-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve(__dirname,'../dashboard/report-mobile.png'),fullPage:true});
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('.report-toolbar').isVisible(),false);
  assert.equal(await page.locator('#report-month').isVisible(),true);
  await page.setViewportSize({width:794,height:1123});
  await page.screenshot({path:path.resolve(__dirname,'../dashboard/report-print-preview.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('Monthly report checked: latest and historical months, signed contributions, text/CSV downloads, print action and layout, mobile overflow, browser errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
