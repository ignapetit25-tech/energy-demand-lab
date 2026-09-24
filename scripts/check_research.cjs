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
  assert.equal(await page.locator('.project').count(),2);
  assert.match(await page.locator('#meter-count').innerText(),/0 de 4/);
  assert.equal(await page.locator('[data-project="camellia_us"]').count(),0);
  await page.screenshot({path:path.resolve(__dirname,'../work/infrastructure-desktop.png'),fullPage:true});
  await page.locator('#country-filter').focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  assert.equal(await page.locator('.project').count(),4);
  await page.locator('[data-project="colossus2_us"] summary').click();
  assert.match(await page.locator('[data-project="colossus2_us"] details').innerText(),/no un fallo/);
  const pending=page.waitForEvent('download');await page.locator('a[download]').click();const download=await pending;
  const stream=await download.createReadStream();let text='';for await(const chunk of stream)text+=chunk;
  const json=JSON.parse(text);assert.equal(json.projects.length,4);assert.equal(json.projects[0].measured_energy_gwh,null);
  await page.selectOption('#country-filter','Estados Unidos');assert.equal(await page.locator('.project').count(),2);
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve(__dirname,'../work/infrastructure-mobile.png'),fullPage:true});
  await page.goto(base+'monthly-report.html');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.deepEqual(errors,[]);
  console.log('Research checked: source table, month mismatch, geography filters, keyboard, legal distinctions, JSON download and mobile overflow.');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exit(1)});
