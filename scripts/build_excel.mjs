import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const python='/home/ignaciopdm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const source=JSON.parse(await fs.readFile(path.join(root,'data/sector_source_manifest.json'),'utf8'));
const raw=JSON.parse(execFileSync(python,['-c',"import csv,json,sys; print(json.dumps(list(csv.DictReader(open(sys.argv[1])))))",path.join(root,source.local_file)],{encoding:'utf8'}));
const latest=JSON.parse(await fs.readFile(path.join(root,`reports/monthly/${source.coverage.end.slice(0,7)}.json`),'utf8'));
const output=path.join(root,'dashboard/downloads');
const work=path.join(root,'work/excel');
await fs.mkdir(output,{recursive:true});await fs.mkdir(work,{recursive:true});
const fresh=process.argv.includes('--rebuild-base');
const wb=fresh?Workbook.create():await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(output,'energy-demand.xlsx')));
const report=fresh?wb.worksheets.add('Informe'):wb.worksheets.getItem('Informe');
const data=fresh?wb.worksheets.add('Datos'):wb.worksheets.getItem('Datos');
const evidence=JSON.parse(await fs.readFile(path.join(root,'data/ai_energy_evidence.json'),'utf8'));
const ai=fresh?wb.worksheets.add('IA y energía'):wb.worksheets.getItem('IA y energía');
wb.recalculate();
const serialValue=v=>v instanceof Date?(v.getTime()-Date.UTC(1899,11,30))/86400000:v;
const preserved=[report,data,ai].map(sh=>({name:sh.name,formulas:JSON.stringify(sh.getUsedRange().formulas),values:sh.getUsedRange().values.map(row=>row.map(serialValue))}));
if(process.argv.includes('--alerts-only')) {
 await extendAlertsWorkbook(wb,root,output,work);
 process.exit(0);
}
const dateSerial=p=>Math.round((Date.parse(p+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000);
const start=10,end=start+raw.length-1,dates=`'Datos'!$A$${start}:$A$${end}`;
const num='#,##0.0;[Red](#,##0.0);0.0';
const pct='+0.0%;[Red]-0.0%;0.0%';
if(fresh){
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
}
const concentration=JSON.parse(await fs.readFile(path.join(root,'dashboard/downloads/concentration_analysis.json'),'utf8'));
const history=JSON.parse(await fs.readFile(path.join(root,'data/activity_monthly_history.json'),'utf8'));
const monthlyResearch=JSON.parse(await fs.readFile(path.join(root,'data/aluar_monthly_research.json'),'utf8'));
const extraSheet=name=>{try{return wb.worksheets.getItem(name);}catch{return wb.worksheets.add(name);}};
const diagnosis=extraSheet('Concentración'),aluar=extraSheet('Aluar'),activities=extraSheet('Actividades');
const names=Object.fromEntries(concentration.branch_labels.map(b=>[b.id,b.label]));
function formatNew(sh,last,widths){
 sh.showGridLines=false;sh.tabColor='#175E4B';
 sh.getRange(`A1:J${last}`).format={font:{name:'Arial',size:11,color:'#203B35'},rowHeight:24,verticalAlignment:'center'};
 for(const [col,width] of Object.entries(widths))sh.getRange(`${col}1:${col}${last}`).format.columnWidth=width;
}
function title(sh,text){sh.getRange('A2').values=[[text]];sh.getRange('A2').format.font={size:17,bold:true,color:'#175E4B'};}
function band(sh,row,labels){const endCol=String.fromCharCode(64+labels.length);sh.getRange(`A${row}:${endCol}${row}`).values=[labels];sh.getRange(`A${row}:${endCol}${row}`).format={fill:'#175E4B',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:42,horizontalAlignment:'center'};}
function text(sh,row,value){sh.getRange(`A${row}`).values=[[value]];}
formatNew(diagnosis,85,{A:31,B:23,C:23,D:23,E:23,F:23,G:23,H:18,I:3,J:65});title(diagnosis,'Concentración del crecimiento eléctrico');
text(diagnosis,4,'Mes vinculado a Informe');diagnosis.getRange('B4').formulas=[["='Informe'!B4"]];diagnosis.getRange('B4').setNumberFormat('mmm yyyy');
text(diagnosis,5,'Demanda nacional. Mes y acumulado enero al mes seleccionado. Fuente original en Datos.');
band(diagnosis,7,['Sector','Cambio mes GWh','% aumento mes','Aporte mes pp','Cambio YTD GWh','% aumento YTD','Aporte YTD pp']);
for(let i=0;i<3;i++){const r=8+i,m=10+i,y=19+i;diagnosis.getRange(`A${r}:G${r}`).formulas=[[
 `='Informe'!A${m}`,`='Informe'!D${m}`,`=IF(ISNUMBER('Informe'!D13),IF('Informe'!D13>0,B${r}/'Informe'!D13,"n.a."),"n.a.")`,`='Informe'!F${m}`,
 `='Informe'!D${y}`,`=IF(ISNUMBER('Informe'!D22),IF('Informe'!D22>0,E${r}/'Informe'!D22,"n.a."),"n.a.")`,`='Informe'!F${y}`]];}
for(const col of ['B','E'])diagnosis.getRange(`${col}8:${col}10`).setNumberFormat(num);
for(const col of ['C','F'])diagnosis.getRange(`${col}8:${col}10`).setNumberFormat(pct);
for(const col of ['D','G'])diagnosis.getRange(`${col}8:${col}10`).setNumberFormat('+0.00;[Red]-0.00;0.00');
text(diagnosis,12,'El % del aumento usa el cambio neto como denominador. Puede superar 100%; si el total no crece, n.a.');
text(diagnosis,14,'Grandes demandas: muestra mensual GUMA/GUME/GUDI, distinta de GUMAs + AUTO de Actividades.');
text(diagnosis,15,'Cobertura declarada: 98% hasta julio de 2026; 90% en agosto. No se confirmó el motivo.');
text(diagnosis,17,'Disponibilidad por ramas');
diagnosis.getRange('B17').formulas=[['=IF(COUNTIFS($A$34:$A$81,$B$4)=4,"Disponible","Sin apertura")']];
band(diagnosis,20,['Componente','Actual MW','Anterior MW','Cambio MW','Aporte pp','% aumento neto','% nivel actual']);
for(let i=0;i<4;i++){const r=21+i;diagnosis.getRange(`A${r}`).values=[[names[concentration.branch_labels[i].id]]];diagnosis.getRange(`B${r}:G${r}`).formulas=[[
 `=IF($B$17="Disponible",SUMIFS($C$34:$C$81,$A$34:$A$81,$B$4,$B$34:$B$81,A${r}),"n.a.")`,
 `=IF($B$17="Disponible",SUMIFS($D$34:$D$81,$A$34:$A$81,$B$4,$B$34:$B$81,A${r}),"n.a.")`,
 `=IF($B$17="Disponible",B${r}-C${r},"n.a.")`,`=IF($B$17="Disponible",D${r}/$C$25*100,"n.a.")`,
 `=IF($B$17="Disponible",IF($D$25>0,D${r}/$D$25,"n.a."),"n.a.")`,`=IF($B$17="Disponible",B${r}/$B$25,"n.a.")`]];}
text(diagnosis,25,'Total publicado');diagnosis.getRange('B25:D25').formulas=[[
 '=IF(B17="Disponible",SUMIFS($F$34:$F$81,$A$34:$A$81,$B$4,$B$34:$B$81,$A$21),"n.a.")',
 '=IF(B17="Disponible",SUMIFS($G$34:$G$81,$A$34:$A$81,$B$4,$B$34:$B$81,$A$21),"n.a.")','=IF(B17="Disponible",B25-C25,"n.a.")']];
diagnosis.getRange('B21:D25').setNumberFormat('#,##0');diagnosis.getRange('E21:E24').setNumberFormat('+0.00;[Red]-0.00;0.00');diagnosis.getRange('F21:G24').setNumberFormat('0.0%');
text(diagnosis,27,'Residuo redondeo MW');diagnosis.getRange('B27').formulas=[['=IF(B17="Disponible",D25-SUM(D21:D24),"n.a.")']];diagnosis.getRange('B27').setNumberFormat('0');
text(diagnosis,29,'Datos por publicación. No se suman potencias de meses distintos ni se atribuyen causas.');
band(diagnosis,33,['Mes','Componente','Actual MW','Anterior MW','Tasa publicada','Total actual MW','Total anterior MW','Cobertura %']);
diagnosis.getRange('J33').values=[['Fuente original (PDF)']];
const branchInput=concentration.branch_comparisons.flatMap(p=>p.rows.map(r=>{const s=concentration.branch_sources.find(s=>s.period===p.period);return [dateSerial(p.period),names[r.id],r.current_mw,r.previous_mw,r.yoy_percent/100,p.total.current_mw,p.total.previous_mw,s.coverage_percent/100,null,s.download_url];}));
diagnosis.getRange('A34:J81').values=branchInput;diagnosis.getRange('A34:A81').setNumberFormat('mmm yyyy');diagnosis.getRange('E34:E81').setNumberFormat(pct);diagnosis.getRange('H34:H81').setNumberFormat('0%');
diagnosis.getRange('B34:B81').format.wrapText=true;diagnosis.getRange('A34:J81').format.rowHeight=42;diagnosis.getRange('A34:A81').setNumberFormat('mmm yyyy"  "');

formatNew(aluar,115,{A:43,B:22,C:22,D:22,E:22,F:22,G:26,H:22,I:23,J:30});title(aluar,'Aluar: consumo y abastecimiento');
text(aluar,4,'Puerto Madryn, División Primario. Comparación anual julio-junio, separada del mes de agosto.');
band(aluar,6,['Indicador','Unidad','2024-2025','2025-2026','Cambio','Variación']);
const annualMetrics=[['production_tonnes','Producción aluminio líquido','t'],['electricity_mwh','Consumo eléctrico total','MWh'],['grid_contract_mwh','Sistema nacional / Futaleufú','MWh'],['thermal_self_supply_mwh','Abastecimiento térmico propio','MWh'],['wind_self_supply_mwh','Abastecimiento eólico propio','MWh'],['unreconciled_mwh','Residuo documental','MWh']];
annualMetrics.forEach(([id,label,unit],i)=>{const r=7+i;aluar.getRange(`A${r}:D${r}`).values=[[label,unit,...concentration.evidence.aluar.observations.map(o=>o[id])]];aluar.getRange(`E${r}:F${r}`).formulas=[[`=D${r}-C${r}`,`=IF(C${r}=0,"n.a.",E${r}/C${r})`]];});
aluar.getRange('C7:E12').setNumberFormat('#,##0');aluar.getRange('F7:F12').setNumberFormat(pct);
text(aluar,14,'Balance anual del cambio (MWh)');aluar.getRange('C14').formulas=[['=SUM(E9:E12)']];aluar.getRange('C14').setNumberFormat('#,##0');
text(aluar,15,'El residuo de 385 MWh de 2025 se conserva: no es una tecnología de generación.');
text(aluar,17,'Datos mensuales: energía neta tomada de la red, calculada desde MW medios diarios.');
text(aluar,18,'Las cinco columnas faltantes quedan vacías. No se distribuye producción trimestral entre meses.');
text(aluar,19,'Sin balance bruto ni autogeneración utilizada, no se identifica la causa mensual ni el aporte de IA.');
band(aluar,21,['Mes','Días','Red MW medios','Red neta GWh','Producción t','Consumo bruto MWh','Térmica utilizada MWh','Eólica utilizada MWh','Ventas y pérdidas MWh','Estado del período']);
aluar.getRange('J21').values=[['Estado del período']];
history.monthly.forEach((p,i)=>{const r=22+i;aluar.getRange(`A${r}:J${r}`).values=[[dateSerial(p.period+'-01'),p.days,p.mw.aluar,null,null,null,null,null,null,p.complete_month?'Completo':'Parcial: '+p.end]];aluar.getRange(`D${r}`).formulas=[[`=C${r}*B${r}*$B$82/$B$83`]];});
aluar.getRange('A22:A78').setNumberFormat('mmm yyyy');aluar.getRange('C22:D78').setNumberFormat('#,##0.0');
text(aluar,80,'Insumos y fuentes: conversiones exactas y datos operativos provisionales.');
aluar.getRange('A82:B83').values=[['Horas por día',24],['MWh por GWh',1000]];
text(aluar,85,'CAMMESA, base diaria capturada el 26/09/2026; hoja Base Detalle diaria GUMAs ACT, columna Z.');text(aluar,86,history.source.url);
text(aluar,88,'Las memorias anuales declaran consumos y fuentes. Fuentes originales:');
text(aluar,89,concentration.evidence.sources[0].url);text(aluar,90,concentration.evidence.sources[1].url);
text(aluar,92,'Trimestre julio-septiembre 2025: 113.363 t. Ventas eólicas/térmicas: 81,8 GWh. No son autoconsumo mensual.');text(aluar,93,monthlyResearch.sources[1].url);
text(aluar,95,'Faltan producción, consumo bruto, autogeneración utilizada, ventas/inyecciones y pérdidas para agosto.');
text(aluar,96,'Los informes privados MEMNet requieren acceso autorizado. No se enviaron solicitudes ni se accedió a datos privados.');
aluar.freezePanes.freezeRows(2);

const activityEnd=10+history.monthly.length*14-1;
formatNew(activities,activityEnd+5,{A:16,B:43,C:27,D:11,E:16,F:19,G:19,H:19,I:18,J:25});title(activities,'Historia eléctrica por actividad');
text(activities,3,'GUMAs + AUTO. 56 meses completos: enero 2022-agosto 2026. Septiembre parcial, 1-23.');
text(activities,4,'Promedios de todos los días. Usuarios vigentes, no panel fijo. No equivale a GUMA/GUME/GUDI.');
text(activities,5,history.source.url);
text(activities,6,'Fuente: hoja Base Detalle diaria GUMAs ACT. Columnas I:X, excluyendo subtotales. Captura 26/09/2026.');
text(activities,7,'Agosto: PDF 17/09 = 2.293,1 MW; PDF 24/09 = 2.295,2 MW; esta base = 2.292,0 MW. Causa sin confirmar.');
band(activities,9,['Mes','Actividad','Rama','Días','Período','MW medios','MW año anterior','Interanual','% de rama','Rama MW medios']);
let rr=10;for(const p of history.monthly){for(const a of history.activities){const r=rr++,prior=r-12*14;
 activities.getRange(`A${r}:J${r}`).values=[[dateSerial(p.period+'-01'),a.label,names[a.branch],p.days,p.complete_month?'Completo':'Parcial',p.mw[a.id],null,null,null,p.mw[a.branch]]];
 activities.getRange(`G${r}:I${r}`).formulas=[[
 prior>=10&&p.complete_month?`=F${prior}`:'="n.a."',
 `=IF(ISNUMBER(G${r}),IF(G${r}=0,"n.a.",F${r}/G${r}-1),"n.a.")`,`=F${r}/J${r}`]];
}}
activities.getRange(`A10:A${activityEnd}`).setNumberFormat('mmm yyyy');activities.getRange(`F10:G${activityEnd}`).setNumberFormat('#,##0.0');activities.getRange(`J10:J${activityEnd}`).setNumberFormat('#,##0.0');activities.getRange(`H10:H${activityEnd}`).setNumberFormat(pct);activities.getRange(`I10:I${activityEnd}`).setNumberFormat('0.0%');activities.getRange(`F10:J${activityEnd}`).format.horizontalAlignment='right';
activities.getRange(`B10:C${activityEnd}`).format.wrapText=true;activities.getRange(`A10:J${activityEnd}`).format.rowHeight=65;
if(!activities.tables.items.length){const table=activities.tables.add(`A9:J${activityEnd}`,true,'HistoriaActividades');table.showFilterButton=true;}
activities.tables.items[0].style='TableStyleLight1';
activities.getRange(`A10:A${activityEnd}`).setNumberFormat('mmm yyyy"  "');activities.getRange(`D10:D${activityEnd}`).setNumberFormat('0"  "');
activities.freezePanes.freezeRows(9);
wb.recalculate();
const near=(a,b)=>assert.ok(Math.abs(a-b)<.00002,`${a} != ${b}`);
near(report.getRange('B13').values[0][0],latest.total.current_gwh);near(report.getRange('E13').values[0][0],latest.total.yoy_percent/100);near(report.getRange('B22').values[0][0],latest.ytd.current_gwh);
near(ai.getRange('B23').values[0][0],70/800);near(ai.getRange('B8').values[0][0],latest.sectors[1].yoy_percent/100);
near(diagnosis.getRange('C8').values[0][0],latest.sectors[0].delta_gwh/latest.total.delta_gwh);
near(diagnosis.getRange('F24').values[0][0],171/131);
near(aluar.getRange('D65').values[0][0],279.532209);near(aluar.getRange('D77').values[0][0],407.095973);
near(aluar.getRange('C14').values[0][0],112918);
const augustActivityRow=10+55*14;near(activities.getRange(`H${augustActivityRow}`).values[0][0],history.monthly[55].yoy_percent.ports/100);
assert.equal(activities.getRange(`H${10+56*14}`).values[0][0],'n.a.');
const originalPower=aluar.getRange('C77').values[0][0];aluar.getRange('C77').values=[[0]];wb.recalculate();near(aluar.getRange('D77').values[0][0],0);aluar.getRange('C77').values=[[originalPower]];
report.getRange('B4').values=[[dateSerial('2025-08-01')]];wb.recalculate();near(report.getRange('B13').values[0][0],11718.756339);
report.getRange('B4').values=[[dateSerial('2027-08-01')]];wb.recalculate();assert.equal(report.getRange('B13').values[0][0],'n.a.');
assert.equal(diagnosis.getRange('F24').values[0][0],'n.a.');assert.equal(diagnosis.getRange('C8').values[0][0],'n.a.');
report.getRange('B4').values=[[dateSerial('2026-02-01')]];wb.recalculate();assert.equal(diagnosis.getRange('F24').values[0][0],'n.a.');
report.getRange('B4').values=[[dateSerial(source.coverage.end)]];wb.recalculate();
if(!fresh)for(const p of preserved){const sh=wb.worksheets.getItem(p.name);assert.equal(JSON.stringify(sh.getUsedRange().formulas),p.formulas,'Preserve formulas: '+p.name);sh.getUsedRange().values.forEach((row,i)=>row.forEach((value,j)=>{const a=serialValue(value),b=p.values[i][j];if(typeof a==='number'&&typeof b==='number')near(a,b);else assert.equal(a,b,`${p.name} row ${i+1} col ${j+1}`);}));}
console.log((await wb.inspect({kind:'table',range:'Informe!A9:G13',include:'values,formulas',tableMaxRows:5,tableMaxCols:7,maxChars:2500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});console.log(errors.ndjson);
for(const [sheetName,range,name] of [['Concentración','A1:G29','concentracion'],['Concentración','A33:H39','concentracion-datos'],['Aluar','A1:H25','aluar'],['Aluar','A73:J78','aluar-reciente'],['Actividades','A1:J15','actividades'],['Actividades',`A${augustActivityRow}:J${augustActivityRow+13}`,'actividades-agosto']]){const image=await wb.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(work,`${name}.png`),new Uint8Array(await image.arrayBuffer()));}
const destination=path.join(output,'energy-demand.xlsx');const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(destination);
const digest=crypto.createHash('sha256').update(await fs.readFile(destination)).digest('hex');
const researchHashes={};for(const p of ['data/concentration_evidence.json','data/sector_history.json','data/activity_monthly_history.json','data/aluar_monthly_research.json'])researchHashes[p]=crypto.createHash('sha256').update(await fs.readFile(path.join(root,p))).digest('hex');
await fs.writeFile(path.join(output,'excel-manifest.json'),JSON.stringify({file:'energy-demand.xlsx',source_sha256:source.sha256,evidence_sha256:crypto.createHash('sha256').update(await fs.readFile(path.join(root,'data/ai_energy_evidence.json'))).digest('hex'),research_sha256:researchHashes,research_reviewed_at:'2026-09-26',latest_period:source.coverage.end,downloaded_at:source.downloaded_at,sha256:digest,default_month:source.coverage.end,month_selector:'Informe!B4'},null,2)+'\n');
console.log('Excel exported and formula recalculation checked for current, historical and missing months.');

async function extendAlertsWorkbook(book,repo,out,previewDir) {
 const alerts=JSON.parse(await fs.readFile(path.join(repo,'dashboard/downloads/sector_alerts.json'),'utf8'));
 const history=JSON.parse(await fs.readFile(path.join(repo,'data/activity_monthly_history.json'),'utf8'));
 const production=JSON.parse(await fs.readFile(path.join(repo,'data/production_history.json'),'utf8'));
 const rawProduction=JSON.parse(await fs.readFile(path.join(repo,'data/production_history_source.json'),'utf8'));
 const oldNames=['Informe','Datos','IA y energía','Concentración','Aluar','Actividades'];
 const before=oldNames.map(name=>{const s=book.worksheets.getItem(name);return {name,values:s.getUsedRange().values.map(row=>row.map(serialValue)),formulas:JSON.stringify(s.getUsedRange().formulas)};});
 const add=name=>{try{return book.worksheets.getItem(name);}catch{return book.worksheets.add(name);}};
 const a=add('Alertas'),p=add('Producción');
 const serial=period=>Math.round((Date.parse(period+'-01T00:00:00Z')-Date.UTC(1899,11,30))/86400000);
 const fmt='#,##0.0;[Red](#,##0.0);0.0';
 function setup(sh,end,widths){sh.showGridLines=false;sh.tabColor='#175E4B';sh.getRange(`A1:M${end}`).format={font:{name:'Arial',size:11,color:'#203B35'},rowHeight:24,verticalAlignment:'center'};for(const [col,width] of Object.entries(widths))sh.getRange(`${col}1:${col}${end}`).format.columnWidth=width;}
 function heading(sh,title){sh.getRange('A2').values=[[title]];sh.getRange('A2').format.font={name:'Arial',size:17,bold:true,color:'#175E4B'};}
 function header(sh,row,labels){sh.getRangeByIndexes(row-1,0,1,labels.length).values=[labels];sh.getRangeByIndexes(row-1,0,1,labels.length).format={fill:'#175E4B',font:{name:'Arial',size:11,color:'#FFFFFF',bold:true},wrapText:true,rowHeight:42,horizontalAlignment:'center'};}
 const first=41,last=first+alerts.periods.length*14-1;
 setup(a,last,{A:51,B:21,C:21,D:21,E:21,F:36,G:17,H:14,I:19,J:18,K:21,L:26,M:65});heading(a,'Alertas sectoriales');
 a.getRange('A3').values=[['Regla base proposal-1. Señales descriptivas, no alarmas calibradas. Aluar se consulta por separado.']];
 a.getRange('A4').values=[['Mes vinculado a Informe!B4']];a.getRange('B4').formulas=[["='Informe'!B4"]];a.getRange('B4').setNumberFormat('mmm yyyy');
 a.getRange('A6:B8').values=[['Observación mínima %',alerts.baseline_rules.watch_yoy_percent/100],['Prioridad mínima %',alerts.baseline_rules.priority_yoy_percent/100],['Persistencia (meses)',alerts.baseline_rules.persistence_months]];
 a.getRange('C6:D7').values=[['Observación MW',alerts.baseline_rules.watch_absolute_mw],['Prioridad MW',alerts.baseline_rules.priority_absolute_mw]];
 a.getRange('B6:B7').setNumberFormat('0%');a.getRange('A9').values=[['Se exigen porcentaje y MW simultáneamente. Persistencia: observación en la misma dirección.']];
 a.getRange('A10').values=[['Cobertura del mes']];a.getRange('B10').formulas=[[`=IF(AND(COUNTIFS($A$${first}:$A$${last},$B$4)=14,COUNTIFS($A$${first}:$A$${last},$B$4,$K$${first}:$K$${last},"No evaluable")=0),"Disponible","No evaluable")`]];
 a.getRange('A11').values=[['Actividades prioritarias']];a.getRange('B11').formulas=[[`=IF(B10="Disponible",COUNTIFS($A$${first}:$A$${last},$B$4,$K$${first}:$K$${last},"Prioridad"),"n.a.")`]];
 a.getRange('A13').values=[['El mes se cambia en Informe. Los umbrales de arriba documentan la base, no un escenario validado.']];
 a.getRange('A14').values=[['Los datos revisados no identifican consumo de IA. No se ajustaron por calendario, clima o usuarios.']];
 header(a,16,['Actividad','Cambio MW','Interanual','Racha observación','Estado','Motivo','Fila de cálculo']);
 const labels=Object.fromEntries(alerts.activities.map(v=>[v.id,v.label]));
 for(let i=0;i<14;i++){
  const r=17+i;a.getRange(`A${r}`).values=[[alerts.activities[i].label]];
  a.getRange(`G${r}`).formulas=[[`=IF(COUNTIFS($A$${first}:$A$${last},$B$4,$B$${first}:$B$${last},A${r})=1,SUMIFS($M$${first}:$M$${last},$A$${first}:$A$${last},$B$4,$B$${first}:$B$${last},A${r}),0)`]];
  a.getRange(`B${r}:F${r}`).formulas=[[...['E','F','I','K','L'].map(c=>`=IF(G${r}=0,"n.a.",INDEX($${c}$${first}:$${c}$${last},G${r}))`)]];
 }
 a.getRange('A17:A30').format.wrapText=true;a.getRange('A17:G30').format.rowHeight=48;a.getRange('B17:B30').setNumberFormat(fmt);a.getRange('C17:C30').setNumberFormat('+0.0%;[Red]-0.0%;0.0%');a.getRange('F17:F30').format.wrapText=true;
 a.getRange('E17:E30').conditionalFormats.clear();
 a.getRange('E17:E30').conditionalFormats.add('containsText',{text:'Prioridad',format:{fill:'#FFF0BF',font:{bold:true}}});
 a.getRange('A32').values=[['Cálculo histórico: 44 meses comparables. Al inicio puede faltar historia para una racha de tres meses.']];
 a.getRange('A33').values=[['Datos eléctricos enlazados a Actividades. La hoja conserva sus originales y fuentes.']];
 a.getRange('A34').values=[['Regla: https://github.com/ignapetit25-tech/energy-demand-lab/blob/main/data/sector_alert_rules.json']];
 a.getRange('A35').values=[['La racha cuenta meses consecutivos con observación y mismo signo, no meses de prioridad por magnitud.']];
 a.getRange('A36').values=[['Futuro: protocolo independiente, octubre 2026–septiembre 2027. No hay resultados prospectivos.']];
 a.getRange('A37').values=[['https://github.com/ignapetit25-tech/energy-demand-lab/blob/main/docs/validacion-sectorial-prospectiva.md']];
 header(a,40,['Mes','Actividad','MW actual','MW año anterior','Cambio MW','Interanual','Observación','Signo','Racha meses','Magnitud alta','Estado','Motivo','Registro']);
 let n=0;
 for(const period of alerts.periods)for(let i=0;i<14;i++){
  const r=first+n++,old=r-14,sourceRow=10+history.monthly.findIndex(m=>m.period===period)*14+i;
  a.getRange(`A${r}:B${r}`).values=[[serial(period),alerts.activities[i].label]];
  a.getRange(`C${r}:M${r}`).formulas=[[
   `=IF(ISNUMBER('Actividades'!F${sourceRow}),'Actividades'!F${sourceRow},"n.a.")`,
   `=IF(ISNUMBER('Actividades'!G${sourceRow}),'Actividades'!G${sourceRow},"n.a.")`,
   `=IF(AND(ISNUMBER(C${r}),ISNUMBER(D${r}),C${r}>=0,D${r}>0),C${r}-D${r},"n.a.")`,
   `=IF(ISNUMBER(E${r}),E${r}/D${r},"n.a.")`,
   `=IF(ISNUMBER(F${r}),IF(AND(ABS(F${r})+0.00000000001>=$B$6,ABS(E${r})+0.000000001>=$D$6),1,0),"n.a.")`,
   `=IF(ISNUMBER(E${r}),SIGN(E${r}),"n.a.")`,
   n<=14?`=IF(ISNUMBER(G${r}),G${r},"n.a.")`:`=IF(NOT(ISNUMBER(G${r})),"n.a.",IF(G${r}=0,0,IF(AND(B${r}=B${old},A${r}=EDATE(A${old},1),H${r}=H${old},ISNUMBER(I${old})),I${old}+1,1)))`,
   `=IF(ISNUMBER(F${r}),IF(AND(ABS(F${r})+0.00000000001>=$B$7,ABS(E${r})+0.000000001>=$D$7),1,0),"n.a.")`,
   `=IF(NOT(ISNUMBER(F${r})),"No evaluable",IF(OR(J${r}=1,I${r}>=$B$8),"Prioridad",IF(G${r}=1,"Observar","Sin umbral")))`,
   `=IF(K${r}="No evaluable","Faltan datos",IF(J${r}=1,"Magnitud",IF(I${r}>=$B$8,"Persistencia",IF(G${r}=1,"Cambio del mes","Sin umbral"))))`,
   `=ROW()-${first-1}`]];
 }
 a.getRange(`A${first}:A${last}`).setNumberFormat('mmm yyyy');a.getRange(`C${first}:E${last}`).setNumberFormat(fmt);a.getRange(`F${first}:F${last}`).setNumberFormat('0.0%');a.getRange(`B${first}:B${last}`).format.wrapText=true;a.getRange(`A${first}:M${last}`).format.rowHeight=48;
 if(!a.tables.items.length)a.tables.add(`A40:M${last}`,true,'CalculoAlertas').style='TableStyleLight1';a.freezePanes.freezeRows(4);
 const pf=17,pl=pf+production.comparisons.length-1;
 setup(p,pl,{A:17,B:31,C:19,D:19,E:19,F:20,G:20,H:19,I:19,J:18,K:25,L:25,M:3});heading(p,'Producción y electricidad');
 p.getRange('A3').values=[['43 meses comunes. Enero 2023–julio 2026. Tasas interanuales de series originales, sin ajuste estacional.']];
 p.getRange('A4').values=[['Captura revisada al 26/09/2026. Categorías relacionadas, no establecimientos equivalentes ni consumo de IA.']];
 p.getRange('A5').values=[['Cemento es parcial: incluye solo un componente de cemento y canteras. IPI no mide toneladas en todas las ramas.']];
 header(p,7,['Indicador INDEC','Meses comparables','Igual dirección','Proporción']);
 for(let i=0;i<3;i++){const r=8+i,label=production.summary[i].label;p.getRange(`A${r}`).values=[[label]];p.getRange(`B${r}:D${r}`).formulas=[[`=COUNTIFS($B$${pf}:$B$${pl},A${r})`,`=SUMIFS($J$${pf}:$J$${pl},$B$${pf}:$B$${pl},A${r})`,`=IF(B${r}>0,C${r}/B${r},"n.a.")`]];}
 p.getRange('D8:D10').setNumberFormat('0.0%');p.getRange('A8:A10').format.wrapText=true;p.getRange('A8:D10').format.rowHeight=40;
 p.getRange('A11').values=[['Igual dirección es descriptivo, no acierto prospectivo. No se calculan elasticidades o eficiencia.']];
 p.getRange('A12').values=[[production.source.url]];
 p.getRange('A13').values=[['INDEC cuadros 2 y 3. Captura 26/09/2026. SHA-256: '+production.source.sha256]];
 p.getRange('A14').values=[['Electricidad: fuente CAMMESA de Actividades. Agosto IPI permanece ausente, no cero.']];
 p.getRange('A15').values=[['Índices base 2004=100. La tasa publicada conserva precisión; se contrasta con el índice del mismo mes anterior.']];
 header(p,16,['Mes','Indicador','MW actual','MW año anterior','Electricidad %','Índice IPI','Índice año anterior','IPI publicado %','IPI calculado %','Igual signo 1/0','Celda índice','Celda tasa']);
 for(let i=0;i<production.comparisons.length;i++){
  const v=production.comparisons[i],r=pf+i,m=production.mapping.find(x=>x.electricity_activity_id===v.activity_id);
  const previousPeriod=String(Number(v.period.slice(0,4))-1)+v.period.slice(4);
  const old=rawProduction.observations.find(x=>x.period===previousPeriod&&x.activity_id===v.activity_id);
  p.getRange(`A${r}:L${r}`).values=[[serial(v.period),m.production_label,v.electricity_current_mw,v.electricity_previous_mw,null,v.original_index,old.original_index,v.yoy_percent/100,null,null,v.original_index_cell,v.yoy_percent_cell]];
  p.getRange(`E${r}`).formulas=[[`=IF(AND(ISNUMBER(C${r}),ISNUMBER(D${r}),D${r}>0),C${r}/D${r}-1,"n.a.")`]];
  p.getRange(`I${r}:J${r}`).formulas=[[`=IF(AND(ISNUMBER(F${r}),ISNUMBER(G${r}),G${r}>0),F${r}/G${r}-1,"n.a.")`,`=IF(AND(ISNUMBER(E${r}),ISNUMBER(H${r})),IF(SIGN(E${r})=SIGN(H${r}),1,0),"n.a.")`]];
 }
 p.getRange(`A${pf}:A${pl}`).setNumberFormat('mmm yyyy');for(const col of ['C','D','F','G'])p.getRange(`${col}${pf}:${col}${pl}`).setNumberFormat(fmt);for(const col of ['E','H','I'])p.getRange(`${col}${pf}:${col}${pl}`).setNumberFormat('0.0%');p.getRange(`B${pf}:B${pl}`).format.wrapText=true;p.getRange(`A${pf}:L${pl}`).format.rowHeight=36;
 if(!p.tables.items.length)p.tables.add(`A16:L${pl}`,true,'ContrasteProduccion').style='TableStyleLight1';p.freezePanes.freezeRows(16);
 book.recalculate();
 const close=(x,y)=>assert.ok(typeof x==='number'&&Math.abs(x-y)<1e-8,`${x} != ${y}`);
 const translated={prioridad:'Prioridad',observar:'Observar',sin_umbral:'Sin umbral',no_evaluable:'No evaluable'};
 n=0;for(const period of alerts.periods)for(const activity of alerts.activities){const expected=alerts.baseline[period].rows.find(v=>v.id===activity.id),r=first+n++;assert.equal(a.getRange(`K${r}`).values[0][0],translated[expected.status]);close(a.getRange(`F${r}`).values[0][0],expected.yoy_percent/100);}
 close(a.getRange('B11').values[0][0],6);
 for(let i=0;i<3;i++)close(p.getRange(`C${8+i}`).values[0][0],production.summary[i].matching_direction);
 for(let i=0;i<production.comparisons.length;i++){const r=pf+i;close(p.getRange(`I${r}`).values[0][0],p.getRange(`H${r}`).values[0][0]);}
 const control=book.worksheets.getItem('Informe').getRange('B4'),originalMonth=control.values[0][0];
 for(const period of alerts.periods){control.values=[[serial(period)]];book.recalculate();const count=alerts.baseline[period].rows.filter(v=>v.status==='prioridad').length;close(a.getRange('B11').values[0][0],count);for(let i=0;i<14;i++){const expected=alerts.baseline[period].rows.find(v=>v.id===alerts.activities[i].id);assert.equal(a.getRange(`E${17+i}`).values[0][0],translated[expected.status]);close(a.getRange(`B${17+i}`).values[0][0],expected.delta_mw);}}
 control.values=[[serial('2027-01')]];book.recalculate();assert.equal(a.getRange('B11').values[0][0],'n.a.');
 control.values=[[null]];book.recalculate();assert.equal(a.getRange('B11').values[0][0],'n.a.');
 control.values=[[originalMonth]];
 const rawCell=book.worksheets.getItem('Actividades').getRange('F780'),rawOriginal=rawCell.values[0][0];rawCell.values=[[null]];book.recalculate();assert.equal(a.getRange('B11').values[0][0],'n.a.');rawCell.values=[[0]];book.recalculate();assert.equal(a.getRange('B10').values[0][0],'Disponible');rawCell.values=[[rawOriginal]];
 book.recalculate();
 for(const old of before){const s=book.worksheets.getItem(old.name);assert.equal(JSON.stringify(s.getUsedRange().formulas),old.formulas,'Preserved formulas '+old.name);s.getUsedRange().values.forEach((row,i)=>row.forEach((value,j)=>{const x=serialValue(value),y=old.values[i][j];if(typeof x==='number'&&typeof y==='number')assert.ok(Math.abs(x-y)<0.00002,'Preserved numeric value '+old.name);else assert.equal(x,y,'Preserved value '+old.name);}));}
 console.log((await book.inspect({kind:'table',range:'Alertas!A16:G20',include:'values,formulas',tableMaxRows:5,tableMaxCols:7,maxChars:1800})).ndjson);
 console.log((await book.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:15},summary:'Final alert extension formula scan'})).ndjson);
 for(const [sheetName,range,name] of [['Alertas','A1:G30','alertas'],['Alertas',`A${last-13}:L${last}`,'alertas-calculo'],['Producción','A1:D11','produccion'],['Producción',`A${pl-8}:L${pl}`,'produccion-datos']]){const png=await book.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(previewDir,name+'.png'),new Uint8Array(await png.arrayBuffer()));}
 const destination=path.join(out,'energy-demand.xlsx');await(await SpreadsheetFile.exportXlsx(book)).save(destination);
 const manifest=JSON.parse(await fs.readFile(path.join(out,'excel-manifest.json'),'utf8'));
 for(const file of ['data/sector_alert_rules.json','data/production_history.json'])manifest.research_sha256[file]=crypto.createHash('sha256').update(await fs.readFile(path.join(repo,file))).digest('hex');
 manifest.sha256=crypto.createHash('sha256').update(await fs.readFile(destination)).digest('hex');
 manifest.alert_rule='proposal-1';manifest.production_comparison_periods=43;
 await fs.writeFile(path.join(out,'excel-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('Alert extension verified: 616 classifications, 129 production comparisons, month changes, missing and zero inputs; six original sheets preserved.');
}
