'use strict';
(()=>{
 const s=window.RESEARCH_DATA.sector,c=s.cammesa,n=s.indec;
 const get=id=>document.getElementById(id);
 const num=(v,d=1)=>new Intl.NumberFormat('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
 const escape=v=>String(v).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 get('branch-diagnosis').textContent=c.diagnosis;
 get('branch-coverage').textContent=c.coverage;
 get('branch-caption').textContent='Agosto 2026 frente a agosto 2025 · MW según CAMMESA · tabla de página 4';
 get('branch-rows').innerHTML=c.rows.map(r=>`<tr class="${r.kind}"><th scope="row">${escape(r.label)}</th><td>${num(r.current_mw,0)}</td><td>${num(r.previous_mw,0)}</td><td>${r.yoy_percent>0?'+':''}${num(r.yoy_percent)}%</td></tr>`).join('');
 get('branch-boundary').textContent=c.boundary;
 get('branch-method').textContent=c.method;
 get('branch-source').innerHTML=`Publicación: ${escape(c.publication_date)} · revisión: ${escape(s.reviewed_at)}. <a href="${escape(c.download_url)}" target="_blank" rel="noopener">PDF original de CAMMESA ↗</a><br>SHA-256: <span class="source-note">${escape(c.sha256)}</span>`;
 function render(){
  const period=get('report-period').value,available=period===c.period;
  get('branch-content').hidden=!available;
  get('branch-availability').textContent=available?'Apertura disponible para el mes seleccionado. Universo distinto de las tres categorías nacionales.':'No se incorporó una tabla por ramas para este mes. La apertura disponible es agosto de 2026; no se reutiliza como dato de otros meses.';
  const match=period===n.period,lag=period===n.next_period;
  get('activity-context').textContent=match||lag?`INDEC · julio 2026: ${num(n.current_percent)}% de capacidad utilizada, frente a ${num(n.previous_percent)}% en julio 2025. Publicación: ${n.publication_date}. ${match?'Coincide el mes, pero no los universos estadísticos.':'No describe agosto: es contexto del mes anterior. El dato de agosto estaba anunciado para '+n.next_release_announced+'.'}`:'No se incorporó un indicador de actividad para este mes. La instantánea disponible es julio de 2026; no se traslada a fechas históricas.';
  get('activity-caveat').textContent=n.limitation;
 }
 get('report-period').addEventListener('change',render);
 window.addEventListener('hashchange',render);render();
})();
