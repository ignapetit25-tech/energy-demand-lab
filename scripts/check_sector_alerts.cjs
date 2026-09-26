const { chromium } = require('playwright');
const fs = require('fs/promises');
const path = require('path');
const http = require('http');
const assert = require('assert/strict');
(async()=>{
 const root = path.resolve(__dirname,'../_site');
 const server = http.createServer(async(req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  try{const b=await fs.readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream'});res.end(b);}catch{res.writeHead(404);res.end();}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const base=process.env.SITE_BASE||`http://127.0.0.1:${server.address().port}/`;
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'sector-alerts.html');
  await page.waitForSelector('#alert-rows tr');
  assert.equal(await page.locator('#alert-period option').count(),44);
  assert.equal(await page.locator('#alert-rows tr').count(),14);
  assert.equal(await page.locator('#production-rows tr').count(),3);
  assert.match(await page.locator('#alert-summary').innerText(),/6 actividades en prioridad/);
  assert.match(await page.locator('#sensitivity-summary').innerText(),/entre 4 y 8/);
  const production=await page.locator('#production-rows').innerText();
  assert.match(production,/-43,3%/);assert.match(production,/-8,4%/);
  for(const p of await page.locator('#alert-period option').evaluateAll(x=>x.map(o=>o.value))){
   await page.selectOption('#alert-period',p);
   const expected=await page.evaluate(p=>window.SECTOR_ALERTS.scenarios.find(s=>s.id==='w10-m5-p3').periods[p].prioridad.length,p);
   assert.equal(await page.locator('#alert-rows .status-prioridad').count(),expected);
   assert.equal(await page.locator('#production-rows').innerText(),production);
   assert.doesNotMatch(await page.locator('main').innerText(),/NaN|undefined|Infinity/);
  }
  await page.selectOption('#alert-period','2026-08');
  const unchangedBase=await page.locator('#alert-rows').innerText();
  for(const pct of ['5','10','15'])for(const mw of ['2.5','5','10'])for(const months of ['2','3','4']){
   await page.selectOption('#sensitivity-percent',pct);await page.selectOption('#sensitivity-mw',mw);await page.selectOption('#sensitivity-months',months);
   const expected=await page.evaluate(id=>window.SECTOR_ALERTS.scenarios.find(s=>s.id===id).periods['2026-08'].prioridad.length,`w${pct}-m${mw}-p${months}`);
   assert.equal(await page.locator('#sensitivity-rows td:nth-child(3) .status-prioridad').count(),expected);
   assert.equal(await page.locator('#alert-rows').innerText(),unchangedBase);
  }
  await page.locator('#reset-thresholds').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#sensitivity-percent').inputValue(),'10');
  assert.equal(await page.locator('#sensitivity-mw').inputValue(),'5');
  assert.equal(await page.locator('#sensitivity-months').inputValue(),'3');
  await page.locator('#alert-period').focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  assert.equal(await page.locator('#alert-period').inputValue(),'2023-01');
  await page.selectOption('#alert-period','2026-08');
  const pending=page.waitForEvent('download');await page.locator('a[download]').click();
  const download=await pending, stream=await download.createReadStream();let body='';for await(const c of stream)body+=c;
  const data=JSON.parse(body);assert.equal(data.scenarios.length,31);assert.equal(data.production.source.august_production_yoy_percent,null);
  await page.screenshot({path:path.resolve(__dirname,'../work/alerts-desktop.png'),fullPage:true});
  for(const width of [768,390,320]){
   await page.setViewportSize({width,height:900});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'overflow at '+width);
  }
  await page.setViewportSize({width:390,height:900});
  await page.screenshot({path:path.resolve(__dirname,'../work/alerts-mobile.png'),fullPage:true});
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('thead th').first().evaluate(e=>getComputedStyle(e).position),'static');
  await page.setViewportSize({width:1200,height:900});
  await page.screenshot({path:path.resolve(__dirname,'../work/alerts-print.png'),fullPage:true});
  await page.emulateMedia({media:'screen'});
  await page.goto(base+'sector-alerts.html?period=2026-07');assert.equal(await page.locator('#alert-period').inputValue(),'2026-07');
  for(const entry of ['index.html','monthly-report.html']){await page.goto(base+entry);assert.ok(await page.locator('a[href="sector-alerts.html"]').count()>0);}
  assert.deepEqual(errors,[]);
  console.log('Alerts verified: 44 periods, 27 interactive variants, base unchanged, fixed July comparison, keyboard/reset, JSON, 320–1440 px and print.');
 }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exit(1);});
