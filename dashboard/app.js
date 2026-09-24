'use strict';
const D = window.ENERGY_DATA;
const P = window.PROSPECTIVE_DATA;
const $ = id => document.getElementById(id);
const num = (v, digits = 1) => Number(v).toLocaleString('es-AR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
const date = (v, short = false) => new Date(v.slice(0, 10) + 'T12:00:00Z').toLocaleDateString('es-AR', {month: short ? 'short' : 'long', year: 'numeric', timeZone: 'UTC'});
const F = D.forecasts[D.forecasts.length - 1];
$('cutoff').textContent = date(D.demand.at(-1).indice_tiempo);
$('target').textContent = date(F.target_period);
$('forecast').textContent = num(F.primary_adaptive_annual_change_gwh);
$('baseline').textContent = num(F.seasonal_naive_gwh);
$('delta').textContent = `${num(F.primary_adaptive_annual_change_gwh - F.seasonal_naive_gwh)} GWh frente a la referencia estacional`;
$('window').textContent = `Ventana: ${F.selected_window_months} meses`;
$('finding').textContent = `En la evaluación retrospectiva, el error del modelo adaptativo fue ${num((D.metrics.overall.adaptive_annual_change_honest.mae_gwh / D.metrics.overall.seasonal_naive.mae_gwh - 1) * 100)}% mayor que el de la referencia estacional.`;
$('source').href = D.source.source_page;
$('hashes').textContent = `Descarga de la fuente: ${D.source.downloaded_at}\n\nSHA-256\n` + Object.entries(D.hashes).map(([p,h])=>`${p}\n${h}`).join('\n\n');
let visible = [];
function chart() {
  const count = Number($('range').value);
  visible = count ? D.demand.slice(-count) : D.demand;
  const narrow=window.innerWidth<650;
  const W=narrow?360:1120,H=narrow?240:300,L=narrow?48:64,R=narrow?20:50,T=25,B=38;
  const serial = d => Number(d.slice(0,4))*12 + Number(d.slice(5,7));
  const first=serial(visible[0].indice_tiempo), last=serial(F.target_period);
  const values=visible.map(r=>Number(r.demanda_total)).concat(Number(F.primary_adaptive_annual_change_gwh));
  const low=Math.floor(Math.min(...values)/1000)*1000-500, high=Math.ceil(Math.max(...values)/1000)*1000+500;
  const x=d=>L+(serial(d)-first)/(last-first)*(W-L-R), y=v=>T+(high-v)/(high-low)*(H-T-B);
  let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Demanda mensual observada desde ${date(visible[0].indice_tiempo)} hasta ${date(visible.at(-1).indice_tiempo)}, con pronóstico separado para ${date(F.target_period)}"><title>Demanda mensual en GWh</title>`;
  for(let i=0;i<5;i++){const v=low+(high-low)*i/4;svg+=`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="#e0e5dc"/><text x="${L-12}" y="${y(v)+4}" text-anchor="end">${num(v,0)}</text>`;}
  const path=visible.map((r,i)=>`${i?'L':'M'}${x(r.indice_tiempo)},${y(+r.demanda_total)}`).join(' ');
  svg+=`<path d="${path} L${x(visible.at(-1).indice_tiempo)},${H-B} L${L},${H-B} Z" fill="#175e4b" opacity=".055"/><path d="${path}" fill="none" stroke="#175e4b" stroke-width="2.5"/>`;
  const ticks=narrow?3:5;
  for(let i=0;i<ticks;i++){const r=visible[Math.round(i*(visible.length-1)/(ticks-1))];svg+=`<text x="${x(r.indice_tiempo)}" y="${H-10}" text-anchor="middle">${date(r.indice_tiempo,true)}</text>`;}
  svg+=`<line x1="${x(F.target_period)}" x2="${x(F.target_period)}" y1="${T}" y2="${H-B}" stroke="#b04a20" stroke-dasharray="3 5" opacity=".5"/><circle cx="${x(F.target_period)}" cy="${y(+F.primary_adaptive_annual_change_gwh)}" r="6" fill="#b04a20"><title>${date(F.target_period)}: ${num(F.primary_adaptive_annual_change_gwh)} GWh (pronóstico)</title></circle><circle id="selected-dot" r="5" fill="#175e4b" stroke="#fffefa" stroke-width="2"/></svg>`;
  $('chart').innerHTML=svg;
  $('month').max=visible.length-1;$('month').value=visible.length-1;
  function select(){const r=visible[Number($('month').value)];$('monthValue').textContent=`${date(r.indice_tiempo,true)} · ${num(r.demanda_total)} GWh`;$('month').setAttribute('aria-valuetext',$('monthValue').textContent);$('selected-dot').setAttribute('cx',x(r.indice_tiempo));$('selected-dot').setAttribute('cy',y(+r.demanda_total));}
  $('month').oninput=select;select();
}
function evidence(){
  const season=$('season').value, rows=D.predictions.filter(r=>season==='all'||r.season===season);
  const models=[['Referencia estacional','seasonal_naive_gwh','Disponible al pronosticar'],['Modelo adaptativo','adaptive_honest_gwh','Sin temperatura del mes objetivo'],['Adaptativo con temperatura posterior','adaptive_oracle_gwh','Diagnóstico con información futura']];
  const scores=models.map(([label,key,note])=>({label,note,score:rows.reduce((s,r)=>s+Math.abs(+r[key]-r.actual_gwh),0)/rows.length}));
  const max=Math.max(...scores.map(s=>s.score))*1.12;
  $('bars').innerHTML=scores.map(s=>`<div class="bar-row"><div class="bar-label"><span>${s.label}</span><b>${num(s.score)} GWh</b></div><div class="bar-track"><div class="bar-fill" style="width:${s.score/max*100}%"></div></div><small>${s.note}</small></div>`).join('');
  const delta=(scores[1].score/scores[0].score-1)*100;
  $('comparison').textContent=`El modelo adaptativo tuvo ${num(Math.abs(delta))}% ${delta>=0?'más':'menos'} error que la referencia en esta selección.`;
  $('sample').textContent=`${rows.length} meses · enero 2016–agosto 2026. Otoño y primavera: marzo–mayo y septiembre–noviembre. Rezago supuesto de demanda: 2 meses. Series históricas descargadas en 2026; no son archivos de cada publicación original.`;
  $('history').innerHTML=rows.map(r=>`<tr><td>${date(r.period,true)}</td>${['actual_gwh','seasonal_naive_gwh','adaptive_honest_gwh','adaptive_oracle_gwh'].map(k=>`<td>${num(r[k])}</td>`).join('')}</tr>`).join('');
}
const outcomes=new Map(P.records.map(r=>[r.target_period,r]));
$('forecast-status').textContent=outcomes.get(F.target_period)?.status==='evaluated'?'Evaluado':'Pendiente de evaluación';
$('prospective-summary').textContent=P.evaluated_months?`${P.evaluated_months} meses evaluados · ${P.pending_months} pendientes. MAE del modelo: ${num(P.metrics.overall.models.primary.mae_gwh)} GWh; referencia: ${num(P.metrics.overall.models.benchmark.mae_gwh)} GWh. Seguimiento descriptivo.`:`${P.pending_months} pronóstico pendiente. Todavía no hay resultados observados registrados: los errores no se calculan ni se muestran como cero.`;
$('forecasts').innerHTML=D.forecasts.map(f=>{const o=outcomes.get(f.target_period),done=o?.status==='evaluated';return `<tr><td>${date(f.target_period)}</td><td>${f.issue_timestamp.slice(0,10)}<br><small>${f.issue_timestamp.slice(11)} · hora de emisión</small></td><td>${num(f.primary_adaptive_annual_change_gwh)}</td><td>${num(f.seasonal_naive_gwh)}</td><td class="${done?'':'pending'}">${done?`${num(o.actual_gwh)} GWh<br><small>Registrado: ${o.captured_at.slice(0,10)}</small>`:'Pendiente · sin evaluar'}</td><td>${done?num(o.errors.primary.signed_gwh):'—'}</td><td>${done?num(o.errors.benchmark.absolute_gwh):'—'}</td></tr>`;}).join('');
$('download').onclick=()=>{const rows=D.forecasts.map(f=>{const o=outcomes.get(f.target_period);return {...f,status:o.status,actual_gwh:o.actual_gwh,primary_signed_error_gwh:o.errors?.primary.signed_gwh,primary_absolute_error_gwh:o.errors?.primary.absolute_gwh,benchmark_absolute_error_gwh:o.errors?.benchmark.absolute_gwh,captured_at:o.captured_at,publication_date:o.publication_date,source_url:o.source_url,source_sha256:o.source_sha256};});const keys=Object.keys(rows[0]);const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';const csv=[keys.map(quote).join(','),...rows.map(r=>keys.map(k=>quote(r[k])).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='energy-demand-pronosticos.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('range').onchange=chart;$('season').onchange=evidence;chart();evidence();
window.addEventListener('resize',chart);
