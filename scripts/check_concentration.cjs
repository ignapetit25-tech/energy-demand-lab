const {chromium}=require('playwright');
const path=require('path');
const assert=require('assert/strict');
const http=require('http');
const fs=require('fs/promises');
(async()=>{
 const root=path.resolve(__dirname,'../dashboard');
 const server=http.createServer(async(req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  try{const bytes=await fs.readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream'});res.end(bytes);}
  catch{res.writeHead(404);res.end();}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const base=process.env.SITE_BASE||`http://127.0.0.1:${server.address().port}/`;
  await page.goto(base+'concentration.html');
  await page.waitForSelector('#granular-rows tr');
  assert.equal(await page.locator('#history-monthly-period option').count(),56);
  assert.equal(await page.locator('#history-monthly-rows tr').count(),14);
  assert.match(await page.locator('#history-monthly-finding').innerText(),/10 de 14/);
  assert.match(await page.locator('#aluar-monthly-finding').innerText(),/407,1 GWh/);
  assert.match(await page.locator('#history-revision-note').innerText(),/2292,0401/);
  for(const p of ['2022-01','2023-01','2024-02','2025-08','2026-08']){
   await page.selectOption('#history-monthly-period',p);
   assert.doesNotMatch(await page.locator('#monthly-history').innerText(),/NaN|undefined|Infinity/);
  }
  await page.selectOption('#history-monthly-period','2022-01');assert.match(await page.locator('#history-monthly-rows').innerText(),/No disponible/);
  await page.selectOption('#history-monthly-period','2026-08');
  for(const id of await page.locator('#history-monthly-activity option').evaluateAll(x=>x.map(o=>o.value))){await page.selectOption('#history-monthly-activity',id);assert.equal(await page.locator('#activity-track-rows tr').count(),5);}
  await page.selectOption('#history-monthly-activity','construction');
  for(const [id,count] of [['national-rows',3],['contribution-rows',4],['annual-rows',5],['granular-rows',14],['pulse-rows',4],['persistence-rows',12]]){
   assert.equal(await page.locator('#'+id+' tr').count(),count);
  }
  assert.equal(await page.locator('#national-kpi').innerText(),'69,4%');
  assert.equal(await page.locator('#aluar-kpi').innerText(),'130,5%');
  assert.match(await page.locator('#annual-finding').innerText(),/\+8,5%/);
  assert.match(await page.locator('#annual-reconciliation').innerText(),/385 MWh/);
  assert.match(await page.locator('#energy-bridge').innerText(),/\+112,918 GWh/);
  assert.match(await page.locator('#pulse-finding').innerText(),/sin Aluar, \+5,8%/);
  await page.locator('#national-window').focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  assert.equal(await page.locator('#national-window').inputValue(),'ytd');
  assert.match(await page.locator('#national-rows').innerText(),/99,8%/);
  const periods=await page.locator('#branch-period option').evaluateAll(options=>options.map(o=>o.value));
  assert.equal(periods.length,12);
  for(const period of periods){
   await page.selectOption('#branch-period',period);
   assert.doesNotMatch(await page.locator('#branches').innerText(),/NaN|undefined|Infinity/);
  }
  await page.selectOption('#branch-period','2026-02-01');
  assert.match(await page.locator('#contribution-rows').innerText(),/No aplicable/);
  await page.selectOption('#branch-period',periods[0]);
  for(const window of ['2026-08','2026-09-partial']){
   await page.selectOption('#activity-window',window);
   for(const [branch,count] of [['all',14],['food_commerce_services',4],['industry',8],['oil_minerals',2]]){
    await page.selectOption('#activity-branch',branch);
    assert.equal(await page.locator('#granular-rows tr').count(),count);
   }
  }
  assert.match(await page.locator('#granular-warning').innerText(),/Mes parcial: solo 16 días/);
  await page.selectOption('#activity-branch','all');
  await page.selectOption('#activity-window','2026-08');
  await page.selectOption('#national-window','month');
  const pending=page.waitForEvent('download');await page.locator('a[download]').first().click();
  const download=await pending,stream=await download.createReadStream();let content='';for await(const chunk of stream)content+=chunk;
  const data=JSON.parse(content);assert.equal(data.evidence.gumas.activities.length,14);
  assert.equal(data.evidence.aluar.monthly_attribution.ai_share_percent,null);
  assert.equal(data.evidence.aluar.observations[0].unreconciled_mwh,385);
  const pendingHistory=page.waitForEvent('download');await page.locator('a[download][href="downloads/activity_monthly_history.json"]').click();
  const dh=await pendingHistory,sh=await dh.createReadStream();let jh='';for await(const c of sh)jh+=c;assert.equal(JSON.parse(jh).daily_count,1727);
  await page.screenshot({path:path.resolve(__dirname,'../work/concentration-desktop.png'),fullPage:true});
  await page.locator('#aluar').screenshot({path:path.resolve(__dirname,'../work/concentration-aluar.png')});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:900});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Page overflow at '+width);
  }
  await page.screenshot({path:path.resolve(__dirname,'../work/concentration-mobile.png'),fullPage:true});
  await page.locator('#activities').screenshot({path:path.resolve(__dirname,'../work/concentration-activities-mobile.png')});
  await page.locator('#monthly-history').screenshot({path:path.resolve(__dirname,'../work/activity-history-mobile.png')});
  assert.deepEqual(errors,[]);
  console.log('Concentration: 12 monthly selections, 8 activity filters, YTD, annual balance, download, keyboard and desktop/mobile checks passed.');
 }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exit(1);});
