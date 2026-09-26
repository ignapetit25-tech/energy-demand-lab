const {chromium}=require('playwright');
const path=require('path');
const assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const base=process.env.SITE_BASE||'file://'+path.resolve(__dirname,'../_site')+'/';
  await page.goto(base+'monthly-report.html');
  assert.equal(await page.locator('#monthly-alert-rows tr').count(),14);
  assert.match(await page.locator('#monthly-alert-note').innerText(),/6 prioridades/);
  assert.equal(await page.locator('#monthly-production-rows tr').count(),0);
  assert.match(await page.locator('#monthly-production-note').innerText(),/Sin contraste IPI del mes 2026-08/);
  assert.match(await page.locator('#monthly-registry-note').innerText(),/0 meses emitidos/);
  const pending=page.waitForEvent('download');await page.click('#export-text');const file=await pending;
  const stream=await file.createReadStream();let text='';for await(const c of stream)text+=c;
  assert.match(text,/15 de 43/);assert.match(text,/Registro prospectivo/);assert.match(text,/Sin contraste IPI del mes 2026-08/);
  await page.selectOption('#report-period','2026-07-01');
  assert.equal(await page.locator('#monthly-production-rows tr').count(),3);
  assert.match(await page.locator('#monthly-production-note').innerText(),/mismo mes: 2026-07/);
  await page.selectOption('#report-period','2022-01-01');
  assert.equal(await page.locator('#monthly-alert-rows tr').count(),0);
  assert.equal(await page.locator('#monthly-production-rows tr').count(),0);
  await page.selectOption('#report-period','2026-08-01');
  await page.locator('#sector-validation').screenshot({path:path.resolve(__dirname,'../work/registry-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.locator('#sector-validation').screenshot({path:path.resolve(__dirname,'../work/registry-mobile.png')});
  await page.emulateMedia({media:'print'});assert.equal(await page.locator('#sector-validation').isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('Registry report: matching months, missingness, TXT, mobile, print and browser errors checked.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
