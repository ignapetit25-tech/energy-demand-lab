'use strict';
(()=>{
 const h=window.RESEARCH_DATA.history,get=id=>document.getElementById(id);
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const num=(v,d=1)=>new Intl.NumberFormat('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
 const signed=(v,d=1)=>(v>0?'+':'')+num(v,d);
 const month=p=>new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(p+'T00:00:00Z'));
 const sources=Object.fromEntries(h.sources.map(s=>[s.period,s]));
 const rate=(s,id)=>s.rows.find(r=>r.id===id).yoy_percent;
 const rises=h.monthly_snapshots.filter(s=>rate(s,'total')>0).length;
 const without=h.monthly_snapshots.filter(s=>rate(s,'without_aluar')>0).length;
 const divergence=h.monthly_snapshots.filter(s=>rate(s,'total')>0&&rate(s,'without_aluar')<0).length;
 get('history-count').textContent=h.historical_observations.length+' observaciones';
 get('recent-finding').textContent='En '+rises+' de los 12 informes crece el total; sin Aluar, crece en '+without+'. En '+divergence+' meses el total aumenta mientras el resto de la muestra cae. Es un recuento de resultados publicados, no una estimación del efecto de Aluar o de IA.';
 get('recent-rows').innerHTML=h.monthly_snapshots.map(s=>'<tr class="'+(sources[s.source_period].coverage_percent===90?'coverage-change':'')+'"><th scope="row">'+esc(month(s.period))+'</th>'+['total','without_aluar','industry','aluar'].map(id=>'<td class="'+(rate(s,id)<0?'decrease':'increase')+'">'+signed(rate(s,id),rate(s,id)*10%1?2:1)+'%</td>').join('')+'<td>'+sources[s.source_period].coverage_percent+'%</td><td><a href="'+esc(sources[s.source_period].download_url)+'" target="_blank" rel="noopener">PDF · p. '+sources[s.source_period].comparison_page+'</a></td></tr>').join('');
 get('calendar-month').innerHTML=Array.from({length:12},(_,i)=>'<option value="'+String(i+1).padStart(2,'0')+'">'+new Intl.DateTimeFormat('es-AR',{month:'long',timeZone:'UTC'}).format(new Date(Date.UTC(2026,i,1)))+'</option>').join('');
 get('calendar-month').value='08';
 get('branch-select').innerHTML=h.branches.map(b=>'<option value="'+b.id+'">'+esc(b.label)+'</option>').join('');get('branch-select').value='industry';
 function renderHistory(){
  const selected=get('calendar-month').value,key=get('branch-select').value;
  const rows=h.historical_observations.filter(r=>r.period.slice(5,7)===selected),first=rows[0],last=rows.at(-1),source=sources[last.source_period];
  const label=h.branches.find(b=>b.id===key).label,change=(last.values[key]/first.values[key]-1)*100;
  get('history-finding').textContent=label+': '+num(last.values[key],0)+' '+source.unit+' en '+month(last.period)+', frente a '+num(first.values[key],0)+' en '+month(first.period)+' ('+signed(change)+'%). Comparación calculada con valores redondeados de una misma publicación.';
  get('history-source').innerHTML='Fuente: <a href="'+esc(source.download_url)+'" target="_blank" rel="noopener">CAMMESA · edición '+esc(month(source.period))+' · página '+source.history_page+' ↗</a>. Cobertura declarada: '+source.coverage_percent+'%. '+esc(source.note)+' En pantallas pequeñas, desplazá el gráfico horizontalmente para ver todos los años.';
  get('history-caption').textContent='Valores publicados para el mismo mes · '+source.unit+' · no energía acumulada';
  get('history-rows').innerHTML=rows.map(r=>'<tr><th scope="row">'+r.period.slice(0,4)+'</th>'+h.branches.map(b=>'<td>'+num(r.values[b.id],0)+'</td>').join('')+'</tr>').join('');
  const w=960,ht=300,left=65,right=25,top=25,bottom=45,max=Math.ceil(Math.max(...rows.map(r=>r.values[key]))/100)*100;
  const x=i=>left+i*(w-left-right)/(rows.length-1),y=v=>ht-bottom-v*(ht-top-bottom)/max;
  let svg='<svg viewBox="0 0 '+w+' '+ht+'" role="img" aria-labelledby="series-title series-desc"><title id="series-title">'+esc(label)+': mismo mes, distintos años</title><desc id="series-desc">'+esc(get('history-finding').textContent)+' Los valores están disponibles en la tabla siguiente.</desc>';
  for(let j=0;j<=4;j++){const v=max*j/4;svg+='<line x1="'+left+'" x2="'+(w-right)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="var(--line)"/><text x="'+(left-10)+'" y="'+(y(v)+4)+'" text-anchor="end">'+num(v,0)+'</text>';}
  svg+='<polyline points="'+rows.map((r,i)=>x(i)+','+y(r.values[key])).join(' ')+'" fill="none" stroke="var(--teal)" stroke-width="3"/>';
  rows.forEach((r,i)=>{svg+='<circle cx="'+x(i)+'" cy="'+y(r.values[key])+'" r="4" fill="var(--teal)"><title>'+r.period.slice(0,4)+': '+r.values[key]+' '+source.unit+'</title></circle>';if(i%2===0||i===rows.length-1)svg+='<text x="'+x(i)+'" y="'+(ht-15)+'" text-anchor="middle">'+r.period.slice(0,4)+'</text>';});
  svg+='<text x="'+left+'" y="15">'+esc(source.unit)+'</text></svg>';get('history-chart').innerHTML=svg;
 }
 const a=h.activity;
 get('activity-period').innerHTML=a.observations.slice().reverse().map(r=>'<option value="'+r.period+'">'+esc(month(r.period))+'</option>').join('');
 get('activity-notes').textContent=a.note;
 function renderActivity(){
  const row=a.observations.find(r=>r.period===get('activity-period').value),previous=a.observations.find(r=>r.period===String(Number(row.period.slice(0,4))-1)+row.period.slice(4));
  const count=previous?a.sectors.filter(s=>row.values[s.id]>previous.values[s.id]).length:null;
  const ranked=a.sectors.slice().sort((s,t)=>row.values[t.id]-row.values[s.id]);
  get('activity-finding').textContent=month(row.period)+': nivel general '+num(row.general_percent)+'%.'+(previous?' '+count+' de 12 actividades superan su utilización de un año antes. Nivel general: '+signed(row.general_percent-previous.general_percent)+' puntos porcentuales.':' No se incorporó el mismo mes del año anterior; la comparación interanual queda sin dato.')+' Mayor utilización: '+ranked[0].label+' ('+num(row.values[ranked[0].id])+'%); menor: '+ranked.at(-1).label+' ('+num(row.values[ranked.at(-1).id])+'%).';
  get('activity-caption').textContent='Capacidad utilizada · '+month(row.period)+' · ordenada de mayor a menor nivel';
  get('activity-rows').innerHTML=ranked.map(s=>'<tr><th scope="row">'+esc(s.label)+'</th><td>'+num(row.values[s.id])+'%</td><td>'+(previous?num(previous.values[s.id])+'%':'No incorporado')+'</td><td>'+(previous?signed(row.values[s.id]-previous.values[s.id])+' pp':'—')+'</td></tr>').join('');
 }
 get('history-method').textContent=h.method;
 get('source-list').innerHTML=h.sources.map(s=>'<li><a href="'+esc(s.download_url)+'" target="_blank" rel="noopener">'+esc(month(s.period))+'</a> · publicación '+esc(s.publication_date)+' · páginas '+s.comparison_page+' y '+s.history_page+' · SHA-256 '+esc(s.sha256)+'</li>').join('');
 get('calendar-month').addEventListener('change',renderHistory);get('branch-select').addEventListener('change',renderHistory);get('activity-period').addEventListener('change',renderActivity);renderHistory();renderActivity();
})();
