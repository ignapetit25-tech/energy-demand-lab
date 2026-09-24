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
const evidence=JSON.parse(await fs.readFile(path.join(root,'data/ai_energy_evidence.json'),'utf8'));
const ai=wb.worksheets.add('IA y energía');
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
report.getRange('A42').values=[['IA y electricidad: evidencia internacional y límites de atribución en la hoja IA y energía.']];
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
ai.showGridLines=false;ai.tabColor='#B86838';
ai.getRange('A1:G38').format={font:{name:'Arial',size:11,color:'#203B35'},rowHeight:25,verticalAlignment:'center',wrapText:true};
for(const [col,width] of [['A',42],['B',19],['C',16],['D',12],['E',27],['F',45],['G',28]])ai.getRange(`${col}1:${col}38`).format.columnWidth=width;
function aiText(row,text,height=45){ai.getRange(`A${row}:G${row}`).merge();ai.getRange(`A${row}`).values=[[text]];ai.getRange(`A${row}:G${row}`).format.rowHeight=height;}
aiText(2,'IA y electricidad: evidencia internacional y lectura argentina',35);ai.getRange('A2').format.font={size:17,bold:true,color:'#175E4B'};
aiText(3,`Revisión: ${evidence.reviewed_at}. El contexto internacional no representa la información disponible en cada mes histórico.`,32);
aiText(4,evidence.conclusion,50);
ai.getRange('A6').values=[['Mes local (vinculado a Informe)']];ai.getRange('B6').formulas=[["='Informe'!B4"]];ai.getRange('B6').setNumberFormat('mmm yyyy');
ai.getRange('A7:C7').values=[['Sector argentino','Interanual %','Atribución IA']];
ai.getRange('A8:A9').values=[['Comercio e industria'],['Grandes usuarios']];ai.getRange('B8:B9').formulas=[["='Informe'!E11"],["='Informe'!E12"]];ai.getRange('B8:B9').setNumberFormat(pct);ai.getRange('C8:C9').values=[['No identificable'],['No identificable']];
ai.getRange('D8:G9').merge();ai.getRange('D8').values=[['Variaciones sectoriales no son efectos de IA. No identificable no significa 0 GWh.']];
ai.getRange('A11:G11').values=[['Indicador','Ámbito / período','Valor','Unidad','Tipo de evidencia','Límite de interpretación','Fuente ID']];
for(const row of [7,11])ai.getRange(`A${row}:${row===7?'C':'G'}${row}`).format={fill:'#175E4B',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:38};
const wrap=(text,width)=>text.split(' ').reduce((lines,word)=>{if((lines.at(-1)+' '+word).trim().length>width)lines.push(word);else lines[lines.length-1]=(lines.at(-1)+' '+word).trim();return lines;},['']).join('\n');
ai.getRange('A12:G18').values=evidence.indicators.map(e=>[wrap(e.metric,38),`${e.geography}\n${e.period}`,e.value,e.unit,wrap(e.status,24),wrap(e.limitation,43),e.source_id]);
ai.getRange('A12:G18').format.rowHeight=80;ai.getRange('C12:C18').setNumberFormat('0');ai.getRange('A17:G17').format.fill='#FFF0BF';
aiText(20,'Aporte aproximado de todos los centros de datos al aumento eléctrico mundial de 2025',30);
ai.getRange('A21').values=[['Incremento centros de datos (TWh)']];ai.getRange('B21').formulas=[['=C15']];
ai.getRange('A22').values=[['Incremento mundial total (TWh)']];ai.getRange('B22').formulas=[['=C16']];
ai.getRange('A23').values=[['Aporte al incremento mundial (%)']];ai.getRange('B23').formulas=[['=B21/B22']];ai.getRange('B23').setNumberFormat('0.0%');
ai.getRange('D21:G23').merge();ai.getRange('D21').values=[['Cálculo propio con estimaciones redondeadas de AIE: 70 / 800. No mide el aporte exclusivo de IA ni la participación en el consumo total.']];
aiText(25,evidence.interpretation,65);
aiText(26,evidence.next_data,70);
aiText(28,'Fuentes de los indicadores (la fecha de revisión no es la del dato)',30);
for(let i=0;i<evidence.sources.length;i++){const s=evidence.sources[i];aiText(29+i*2,`${s.id}: ${s.publisher}. ${s.title}`,30);aiText(30+i*2,s.url,35);}
aiText(36,'Unidades: 1 TWh = 1.000 GWh. La tabla combina ámbitos y períodos distintos: sus filas no se suman.',32);
ai.freezePanes.freezeRows(11);
wb.recalculate();
const near=(a,b)=>assert.ok(Math.abs(a-b)<.00002,`${a} != ${b}`);
near(report.getRange('B13').values[0][0],latest.total.current_gwh);near(report.getRange('E13').values[0][0],latest.total.yoy_percent/100);near(report.getRange('B22').values[0][0],latest.ytd.current_gwh);
near(ai.getRange('B23').values[0][0],70/800);near(ai.getRange('B8').values[0][0],latest.sectors[1].yoy_percent/100);
report.getRange('B4').values=[[dateSerial('2025-08-01')]];wb.recalculate();near(report.getRange('B13').values[0][0],11718.756339);
report.getRange('B4').values=[[dateSerial('2027-08-01')]];wb.recalculate();assert.equal(report.getRange('B13').values[0][0],'n.a.');
report.getRange('B4').values=[[dateSerial(source.coverage.end)]];wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Informe!A9:G13',include:'values,formulas',tableMaxRows:5,tableMaxCols:7,maxChars:2500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});console.log(errors.ndjson);
for(const [sheetName,range,name] of [['Informe','A1:G42','informe'],['Datos','A1:E17','datos'],['IA y energía','A1:G18','ia-evidencia'],['IA y energía','A20:G36','ia-metodo']]){const image=await wb.render({sheetName,range,scale:1.4,format:'png'});await fs.writeFile(path.join(work,`${name}.png`),new Uint8Array(await image.arrayBuffer()));}
const destination=path.join(output,'energy-demand.xlsx');const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(destination);
const digest=crypto.createHash('sha256').update(await fs.readFile(destination)).digest('hex');
await fs.writeFile(path.join(output,'excel-manifest.json'),JSON.stringify({file:'energy-demand.xlsx',source_sha256:source.sha256,evidence_sha256:crypto.createHash('sha256').update(await fs.readFile(path.join(root,'data/ai_energy_evidence.json'))).digest('hex'),latest_period:source.coverage.end,downloaded_at:source.downloaded_at,sha256:digest,default_month:source.coverage.end,month_selector:'Informe!B4'},null,2)+'\n');
console.log('Excel exported and formula recalculation checked for current, historical and missing months.');
