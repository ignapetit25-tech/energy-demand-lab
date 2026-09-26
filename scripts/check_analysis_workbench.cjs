const {chromium}=require('playwright');
const assert=require('assert/strict');
const path=require('path');
const http=require('http');
const fs=require('fs');
(async()=>{
 let server;
 let base=process.env.SITE_BASE;
 if(!base){
  const root=path.resolve(__dirname,'../_site');
  server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base=`http://127.0.0.1:${server.address().port}/`;
 }
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'monthly-report.html');
  assert.equal(await page.locator('#executive-findings article').count(),3);
  assert.equal(await page.locator('#quality-sources article').count(),3);
  assert.equal(await page.locator('#monthly-alert-rows .quality-label').count(),14);
  assert.match(await page.locator('#quality-partial').innerText(),/2026-09/);
  assert.match(await page.locator('#document-assistant-status').innerText(),/Exactitud: no medida/);
  assert.match(await page.locator('#operations-state').innerText(),/2026-10/);
  assert.equal(await page.locator('#casebook-hypotheses details').count(),4);
  const summary=page.locator('#casebook-hypotheses summary').first();await summary.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#casebook-hypotheses details').first().getAttribute('open'),'');
  for(const file of ['analysis_workbench.json','document_review_task.json']){
   const pending=page.waitForEvent('download');await page.locator(`a[download][href="downloads/${file}"]`).click();
   const download=await pending,stream=await download.createReadStream();let content='';for await(const c of stream)content+=c;
   const d=JSON.parse(content);assert.ok(file==='analysis_workbench.json'?d.metals.casebook.hypotheses.length===4:d.tasks.length===7);
  }
  const pending=page.waitForEvent('download');await page.click('#export-text');const stream=await(await pending).createReadStream();let text='';for await(const c of stream)text+=c;
  assert.ok(text.indexOf('Resumen ejecutivo')<text.indexOf('Diagnóstico sectorial'));
  assert.match(text,/Dato decisivo/);assert.match(text,/Sin modelo conectado/);
  await page.selectOption('#report-period','2026-07-01');
  assert.match(await page.locator('#monthly-alert-rows').innerText(),/Proxy parcial/);
  await page.selectOption('#report-period','2022-01-01');
  assert.equal(await page.locator('#executive-findings article').count(),0);
  assert.match(await page.locator('#executive-next').innerText(),/No hay prioridades disponibles/);
  await page.selectOption('#report-period','2026-08-01');
  await page.locator('#executive').screenshot({path:path.resolve(__dirname,'../work/executive-desktop.png')});
  for(const width of [320,390,768]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  }
  await page.setViewportSize({width:390,height:844});
  await page.locator('#executive').screenshot({path:path.resolve(__dirname,'../work/executive-mobile.png')});
  await page.locator('#data-quality').screenshot({path:path.resolve(__dirname,'../work/quality-mobile.png')});
  await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
  assert.equal(await page.locator('#casebook-hypotheses details[open]').count(),4);
  await page.emulateMedia({media:'print'});assert.equal(await page.locator('#executive').isVisible(),true);
  await page.evaluate(()=>window.dispatchEvent(new Event('afterprint')));
  assert.equal(await page.locator('#casebook-hypotheses details[open]').count(),1);
  assert.deepEqual(errors,[]);console.log('Workbench verified: dates, quality, missingness, keyboard, downloads, TXT, responsive layout and print.');
 }finally{await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exit(1)});
