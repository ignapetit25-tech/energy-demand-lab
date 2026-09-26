'use strict';
(()=>{
 const d=window.ACTIVITY_HISTORY,get=id=>document.getElementById(id);
 const n=(v,k=1)=>v===null?'No disponible':new Intl.NumberFormat('es-AR',{minimumFractionDigits:k,maximumFractionDigits:k}).format(v);
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const months=d.monthly.filter(r=>r.complete_month),by=Object.fromEntries(d.monthly.map(r=>[r.period,r]));
 get('history-monthly-period').innerHTML=months.slice().reverse().map(r=>'<option value="'+r.period+'">'+r.period+'</option>').join('');
 get('history-monthly-activity').innerHTML=d.activities.map(a=>'<option value="'+a.id+'">'+esc(a.label)+'</option>').join('');
 get('history-monthly-activity').value='construction';
 function draw(){const period=get('history-monthly-period').value,r=by[period],prev=by[(+period.slice(0,4)-1)+period.slice(4)],id=get('history-monthly-activity').value,a=d.activities.find(a=>a.id===id);
  const up=d.activities.filter(a=>r.yoy_percent[a.id]!==null&&r.yoy_percent[a.id]>0).length;
  get('history-monthly-finding').textContent=prev?period+': '+up+' de 14 actividades aumentan respecto al mismo mes del año anterior. Industrias sin Aluar: '+n(r.yoy_percent.industry)+'%. Universo GUMAs + AUTO; no es el total industrial argentino.':'Este mes no tiene comparación interanual dentro de la base incorporada.';
  get('history-monthly-rows').innerHTML=d.activities.map(a=>'<tr><th scope="row">'+esc(a.label)+'</th><td>'+n(r.mw[a.id])+'</td><td>'+n(prev?prev.mw[a.id]:null)+'</td><td>'+(r.yoy_percent[a.id]===null?'No disponible':n(r.yoy_percent[a.id])+'%')+'</td></tr>').join('');
  get('history-monthly-caption').textContent=period+' completo: '+r.days+' días. MW medios calculados desde registros diarios, captura 26/09/2026.';
  const years=months.filter(x=>x.period.slice(5)===period.slice(5));
  get('activity-track-caption').textContent=a.label+' · mismo mes en distintos años · MW medios';
  get('activity-track-rows').innerHTML=years.map(x=>'<tr><th scope="row">'+x.period+'</th><td>'+x.days+'</td><td>'+n(x.mw[id])+'</td><td>'+(x.yoy_percent[id]===null?'No disponible':n(x.yoy_percent[id])+'%')+'</td></tr>').join('');
 }
 get('history-revision-note').textContent=d.revision_comparison.note;
 const x=by['2026-08'],p=by['2025-08'];
 get('aluar-monthly-finding').textContent='Agosto 2025: '+n(p.mw.aluar)+' MW medios, equivalentes a '+n(p.aluar_net_grid_gwh)+' GWh netos de red. Agosto 2026: '+n(x.mw.aluar)+' MW medios, equivalentes a '+n(x.aluar_net_grid_gwh)+' GWh. Cambio: '+n(x.yoy_percent.aluar)+'%. Ambos meses tienen 31 días.';
 get('aluar-research-gap').textContent=d.aluar_research.finding+' Faltan: '+d.aluar_research.missing_fields.join('; ')+'.';
 get('history-monthly-source').innerHTML='<a href="'+esc(d.source.url)+'" target="_blank" rel="noopener">Base oficial de CAMMESA (ZIP con XLSX) ↗</a> · '+d.daily_count+' días, '+d.first_date+' a '+d.last_date+'. Hoja '+esc(d.source.sheet)+'. Archivo SHA-256 '+d.source.sha256;
 get('history-monthly-period').addEventListener('change',draw);get('history-monthly-activity').addEventListener('change',draw);draw();
})();
