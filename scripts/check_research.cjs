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
  try{
   const bytes=await fs.readFile(file);
   const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'}[path.extname(file)]||'application/octet-stream';
   res.writeHead(200,{'Content-Type':mime});res.end(bytes);
  }catch{res.writeHead(404);res.end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.setDefaultTimeout(10000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const base=process.env.SITE_BASE||`http://127.0.0.1:${server.address().port}/`;
  await page.goto(base+'monthly-report.html');
  assert.equal(await page.locator('#branch-rows tr').count(),6);
  assert.match(await page.locator('#branch-diagnosis').innerText(),/sin Aluar cae 1,2%/);
  assert.match(await page.locator('#activity-context').innerText(),/No describe agosto/);
  await page.locator('#sector-depth').screenshot({path:path.resolve(__dirname,'../work/sector-depth.png')});
  await page.selectOption('#report-period','2025-08-01');
  assert.equal(await page.locator('#branch-content').isVisible(),false);
  assert.match(await page.locator('#activity-context').innerText(),/No se incorporó/);
  await page.selectOption('#report-period','2026-07-01');
  assert.match(await page.locator('#activity-context').innerText(),/Coincide el mes/);
  await page.goto(base+'infrastructure.html');
  assert.equal(await page.locator('.project').count(),5);
  assert.match(await page.locator('#meter-count').innerText(),/4 de 5/);
  assert.equal(await page.locator('#argentina-overview tr').count(),5);
  assert.match(await page.locator('[data-project="clementina_xxi"]').innerText(),/233 kW/);
  assert.match(await page.locator('[data-project="cirion_bue1"]').innerText(),/Más de 2 MW/);
  assert.equal(await page.locator('[data-project="camellia_us"]').count(),0);
  await page.screenshot({path:path.resolve(__dirname,'../work/infrastructure-desktop.png'),fullPage:true});
  await page.locator('[data-project="cirion_bue1"]').screenshot({path:path.resolve(__dirname,'../work/cirion-desktop.png')});
  await page.locator('#country-filter').focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  assert.equal(await page.locator('.project').count(),7);
  await page.locator('[data-project="colossus2_us"] summary').click();
  assert.match(await page.locator('[data-project="colossus2_us"] details').innerText(),/no un fallo/);
  const pending=page.waitForEvent('download');await page.locator('a[download]').click();const download=await pending;
  const stream=await download.createReadStream();let text='';for await(const chunk of stream)text+=chunk;
  const json=JSON.parse(text);assert.equal(json.projects.length,7);assert.equal(json.projects[0].measured_energy_gwh,null);
  await page.selectOption('#country-filter','Estados Unidos');assert.equal(await page.locator('.project').count(),2);
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve(__dirname,'../work/infrastructure-mobile.png'),fullPage:true});
  await page.selectOption('#country-filter','Argentina');
  await page.locator('[data-project="clementina_xxi"] summary').click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve(__dirname,'../work/infrastructure-argentina-mobile.png'),fullPage:true});
  await page.locator('[data-project="clementina_xxi"]').screenshot({path:path.resolve(__dirname,'../work/clementina-mobile.png')});
  await page.goto(base+'monthly-report.html');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.goto(base+'sector-history.html');
  assert.equal(await page.locator('#recent-rows tr').count(),12);
  assert.match(await page.locator('#recent-finding').innerText(),/En 6 meses/);
  assert.equal(await page.locator('#history-rows tr').count(),15);
  assert.equal(await page.locator('#activity-rows tr').count(),12);
  assert.match(await page.locator('#activity-finding').innerText(),/6 de 12/);
  assert.match(await page.locator('#activity-rows').innerText(),/-10,7 pp/);
  await page.selectOption('#calendar-month','09');
  assert.equal(await page.locator('#history-rows tr').count(),8);
  await page.selectOption('#activity-period','2025-01-01');
  assert.match(await page.locator('#activity-finding').innerText(),/No se incorporó/);
  await page.selectOption('#activity-period','2026-07-01');
  await page.selectOption('#calendar-month','08');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve(__dirname,'../work/history-mobile.png'),fullPage:true});
  await page.locator('#history').screenshot({path:path.resolve(__dirname,'../work/history-panel-mobile.png')});
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:path.resolve(__dirname,'../work/history-desktop.png'),fullPage:true});
  for(const month of ['01','02','03','04','05','06','07','08','09','10','11','12']){
   await page.selectOption('#calendar-month',month);
   for(const branch of ['industry','food_commerce_services','oil_minerals','aluar']){
    await page.selectOption('#branch-select',branch);
    assert.equal(await page.locator('#history-chart svg').count(),1);
    assert.ok(!(await page.locator('#history-finding').innerText()).includes('NaN'));
   }
  }
  const historyDownload=page.waitForEvent('download');await page.locator('a[download]').click();
  const historyStream=await(await historyDownload).createReadStream();let historyText='';for await(const chunk of historyStream)historyText+=chunk;
  assert.equal(JSON.parse(historyText).historical_observations.length,164);
  assert.deepEqual(errors,[]);
  console.log('Research checked: 12 monthly snapshots, 48 historical selections, 19-month activity dataset, 7 projects, keyboard, legal distinctions, JSON downloads and mobile overflow.');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exit(1)});
