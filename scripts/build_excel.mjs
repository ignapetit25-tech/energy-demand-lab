import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const python='/home/ignaciopdm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const source=JSON.parse(await fs.readFile(path.join(root,'data/sector_source_manifest.json'),'utf8'));
const raw=JSON.parse(execFileSync(python,['-c',"import csv,json,sys; print(json.dumps(list(csv.DictReader(open(sys.argv[1])))))",path.join(root,source.local_file)],{encoding:'utf8'}));
const latest=JSON.parse(await fs.readFile(path.join(root,`reports/monthly/${source.coverage.end.slice(0,7)}.json`),'utf8'));
const output=path.join(root,'dashboard/downloads');
const work=path.join(root,'work/excel');
await fs.mkdir(output,{recursive:true});await fs.mkdir(work,{recursive:true});
const wb=Workbook.create();
const report=wb.worksheets.add('Informe');
const data=wb.worksheets.add('Datos');
const dateSerial=p=>Math.round((Date.parse(p+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000);
const start=10,end=start+raw.length-1,dates=`'Datos'!$A$${start}:$A$${end}`;
const num='#,##0.0;[Red](#,##0.0);0.0';
const pct='+0.0%;[Red]-0.0%;0.0%';
for(const sh of [report,data]){sh.showGridLines=false;sh.getRange(sh===report?'A1:G42':`A1:G${end}`).format.font={name:'Arial',size:11,color:'#203B35'};sh.getRange(sh===report?'A1:G42':`A1:G${end}`).format.rowHeight=23;sh.getRange(sh===report?'A1:G42':`A1:G${end}`).format.verticalAlignment='center';}
report.tabColor='#175E4B';
report.getRange('A1:A42').format.columnWidth=29;
report.getRange('B1:G42').format.columnWidth=19;
report.getRange('A2').values=[['Demanda eléctrica argentina']];report.getRange('A2').format.font={name:'Arial',size:17,bold:true,color:'#175E4B'};
report.getRange('A3').values=[['Diagnóstico mensual por sector · GWh']];
report.getRange('A4').values=[['Mes editable (amarillo)']];report.getRange('B4').values=[[dateSerial(source.coverage.end)]];report.getRange('B4').setNumberFormat('mmm yyyy');report.getRange('B4').format.fill='#FFF0BF';
report.getRange('D4').values=[['Mes de comparación']];report.getRange('E4').formulas=[['=DATE(YEAR(B4)-1,MONTH(B4),1)']];report.getRange('E4').setNumberFormat('mmm yyyy');
report.getRange('B4').dataValidation={rule:{type:'list',formula1:`INDIRECT("'Datos'!$A$${start+12}:$A$${end}")`}};
report.getRange('A5').values=[['Elegí un mes desde ene 2006 hasta ago 2026. Los cálculos y el gráfico se actualizan.']];
report.getRange('A6').values=[['Cobertura mensual']];report.getRange('B6').formulas=[[`=IF(AND(COUNTIFS(${dates},B4)=1,COUNTIFS(${dates},E4)=1),"Disponible","Mes sin cobertura")`]];
function header(row,values){report.getRange(`A${row}:G${row}`).values=[values];report.getRange(`A${row}:G${row}`).format={fill:'#175E4B',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',rowHeight:38};}
header(9,['Sector','Actual GWh','Anterior GWh','Cambio GWh','Interanual %','Aporte (pp)','Peso actual %']);
const labels=['Residencial','Comercio e industria','Grandes usuarios'];
for(let i=0;i<3;i++){
 const row=10+i,col=String.fromCharCode(67+i),vals=`'Datos'!$${col}$${start}:$${col}$${end}`;
 report.getRange(`A${row}`).values=[[labels[i]]];
 report.getRange(`B${row}:G${row}`).formulas=[[
 `=IF($B$6="Disponible",SUMIFS(${vals},${dates},$B$4),"n.a.")`,
 `=IF($B$6="Disponible",SUMIFS(${vals},${dates},$E$4),"n.a.")`,
 `=IF($B$6="Disponible",B${row}-C${row},"n.a.")`,
 `=IF($B$6="Disponible",IF(C${row}=0,"n.a.",D${row}/C${row}),"n.a.")`,
 `=IF($B$6="Disponible",D${row}/$C$13*100,"n.a.")`,
 `=IF($B$6="Disponible",B${row}/$B$13,"n.a.")`]];
}
report.getRange('A13').values=[['Total']];report.getRange('B13:G13').formulas=[['=IF(B6="Disponible",SUM(B10:B12),"n.a.")','=IF(B6="Disponible",SUM(C10:C12),"n.a.")','=IF(B6="Disponible",SUM(D10:D12),"n.a.")','=IF(B6="Disponible",D13/C13,"n.a.")','=IF(B6="Disponible",SUM(F10:F12),"n.a.")','=IF(B6="Disponible",SUM(G10:G12),"n.a.")']];
report.getRange('A15').values=[['Acumulado de enero al mes seleccionado frente al mismo período del año anterior']];
report.getRange('A16').values=[['Cobertura acumulado']];report.getRange('B16').formulas=[[`=IF(AND(COUNTIFS(${dates},">="&DATE(YEAR(B4),1,1),${dates},"<="&B4)=MONTH(B4),COUNTIFS(${dates},">="&DATE(YEAR(E4),1,1),${dates},"<="&E4)=MONTH(E4)),"Disponible","Faltan meses")`]];
header(18,['Sector','Actual GWh','Anterior GWh','Cambio GWh','Interanual %','Aporte (pp)','Peso actual %']);
for(let i=0;i<3;i++){
 const row=19+i,col=String.fromCharCode(67+i),vals=`'Datos'!$${col}$${start}:$${col}$${end}`;
 report.getRange(`A${row}`).values=[[labels[i]]];
 report.getRange(`B${row}:G${row}`).formulas=[[
 `=IF($B$16="Disponible",SUMIFS(${vals},${dates},">="&DATE(YEAR($B$4),1,1),${dates},"<="&$B$4),"n.a.")`,
 `=IF($B$16="Disponible",SUMIFS(${vals},${dates},">="&DATE(YEAR($E$4),1,1),${dates},"<="&$E$4),"n.a.")`,
 `=IF($B$16="Disponible",B${row}-C${row},"n.a.")`,
 `=IF($B$16="Disponible",IF(C${row}=0,"n.a.",D${row}/C${row}),"n.a.")`,
 `=IF($B$16="Disponible",D${row}/$C$22*100,"n.a.")`,
 `=IF($B$16="Disponible",B${row}/$B$22,"n.a.")`]];
}
report.getRange('A22').values=[['Total']];report.getRange('B22:G22').formulas=[['=IF(B16="Disponible",SUM(B19:B21),"n.a.")','=IF(B16="Disponible",SUM(C19:C21),"n.a.")','=IF(B16="Disponible",SUM(D19:D21),"n.a.")','=IF(B16="Disponible",D22/C22,"n.a.")','=IF(B16="Disponible",SUM(F19:F21),"n.a.")','=IF(B16="Disponible",SUM(G19:G21),"n.a.")']];
for(const range of ['B10:D13','B19:D22'])report.getRange(range).setNumberFormat(num);
for(const range of ['E10:E13','E19:E22'])report.getRange(range).setNumberFormat(pct);
for(const range of ['G10:G13','G19:G22'])report.getRange(range).setNumberFormat('0.0%');
for(const range of ['F10:F13','F19:F22'])report.getRange(range).setNumberFormat('+0.00;[Red]-0.00;0.00');
for(const row of [13,22])report.getRange(`A${row}:G${row}`).format={fill:'#E8EDDF',font:{bold:true},borders:{top:{style:'thin',color:'#9CAF9F'}}};
const chart=report.charts.add('bar',report.getRange('A9:C12'));chart.title='Demanda por sector: mes actual y año anterior (GWh)';chart.titleTextStyle.fontSize=14;chart.titleTextStyle.typeface='Arial';chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:11}};chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:11}};chart.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};chart.series.items[0].fill='#175E4B';chart.series.items[1].fill='#98ABA0';chart.setPosition('A25','G37');
report.getRange('A38').values=[['Aporte (pp): cambio del sector / total del período anterior × 100. No es su propia tasa de crecimiento.']];
report.getRange('A39').values=[['Datos sin ajuste climático ni estacional. Los aportes son contables y no identifican causas.']];
report.getRange('A40').values=[['Conciliación con fuente (GWh)']];report.getRange('B40').formulas=[[`=IF(B6="Disponible",B13-SUMIFS('Datos'!$B$${start}:$B$${end},${dates},B4),"n.a.")`]];report.getRange('B40').setNumberFormat('0.000000');
report.getRange('A41').values=[['Datos originales y fuente en la hoja Datos. El archivo no descarga publicaciones nuevas.']];
data.getRange(`A1:A${end}`).format.columnWidth=18;data.getRange(`B1:E${end}`).format.columnWidth=23;
data.getRange('A2').values=[['Datos mensuales originales (GWh)']];data.getRange('A2').format.font={name:'Arial',size:17,bold:true,color:'#175E4B'};
data.getRange('A3').values=[['Fuente: Datos Argentina / CAMMESA. Consulta oficial en el enlace de A4.']];
data.getRange('A4').values=[['https://datos.gob.ar/dataset/sspm-demanda-electricidad']];
data.getRange('A5').values=[[`Descarga: ${source.downloaded_at}. Histórico revisable: enero 2005–agosto 2026.`]];
data.getRange('A6').values=[['Comercio e industria conserva la categoría conjunta de la fuente. Grandes usuarios no equivale a industria.']];
data.getRange('A7').values=[[`SHA-256: ${source.sha256}`]];
data.getRange('A9:E9').values=[['Mes','Total GWh','Residencial GWh','Comercio e industria GWh','Grandes usuarios GWh']];
data.getRange(`A${start}:E${end}`).values=raw.map(r=>[dateSerial(r.period),...['total_gwh','residential_gwh','commerce_industry_gwh','large_users_gwh'].map(k=>Number(r[k]))]);
data.getRange(`A${start}:A${end}`).setNumberFormat('mmm yyyy');data.getRange(`B${start}:E${end}`).setNumberFormat('#,##0.000');
const table=data.tables.add(`A9:E${end}`,true,'DemandaMensual');table.showFilterButton=true;
data.getRange('A9:E9').format={fill:'#175E4B',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',rowHeight:40};data.freezePanes.freezeRows(9);
wb.recalculate();
const near=(a,b)=>assert.ok(Math.abs(a-b)<.00002,`${a} != ${b}`);
near(report.getRange('B13').values[0][0],latest.total.current_gwh);near(report.getRange('E13').values[0][0],latest.total.yoy_percent/100);near(report.getRange('B22').values[0][0],latest.ytd.current_gwh);
report.getRange('B4').values=[[dateSerial('2025-08-01')]];wb.recalculate();near(report.getRange('B13').values[0][0],11718.756339);
report.getRange('B4').values=[[dateSerial('2027-08-01')]];wb.recalculate();assert.equal(report.getRange('B13').values[0][0],'n.a.');
report.getRange('B4').values=[[dateSerial(source.coverage.end)]];wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Informe!A9:G13',include:'values,formulas',tableMaxRows:5,tableMaxCols:7,maxChars:2500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});console.log(errors.ndjson);
for(const [sheetName,range,name] of [['Informe','A1:G42','informe'],['Datos','A1:E17','datos']]){const image=await wb.render({sheetName,range,scale:1.4,format:'png'});await fs.writeFile(path.join(work,`${name}.png`),new Uint8Array(await image.arrayBuffer()));}
const destination=path.join(output,'energy-demand.xlsx');const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(destination);
const digest=crypto.createHash('sha256').update(await fs.readFile(destination)).digest('hex');
await fs.writeFile(path.join(output,'excel-manifest.json'),JSON.stringify({file:'energy-demand.xlsx',source_sha256:source.sha256,latest_period:source.coverage.end,downloaded_at:source.downloaded_at,sha256:digest,default_month:source.coverage.end,month_selector:'Informe!B4'},null,2)+'\n');
console.log('Excel exported and formula recalculation checked for current, historical and missing months.');
