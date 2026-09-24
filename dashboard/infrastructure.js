'use strict';
(()=>{
 const r=window.RESEARCH_DATA.registry,get=id=>document.getElementById(id);
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const sources=Object.fromEntries(r.sources.map(s=>[s.id,s]));
 const sourceLink=id=>{const s=sources[id];return `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.publisher)} · ${esc(s.date)} ↗</a> <span class="source-kind">(${esc(s.type)})</span>`;};
 get('registry-date').textContent=r.reviewed_at;get('registry-scope').textContent=r.scope;get('registry-rules').textContent=r.rules;
 get('project-count').textContent=r.projects.length;get('argentina-count').textContent=r.projects.filter(p=>p.country==='Argentina').length;
 get('meter-count').textContent=`${r.projects.filter(p=>p.measured_energy_gwh!==null).length} de ${r.projects.length}`;
 function render(){
  const filter=get('country-filter').value,projects=r.projects.filter(p=>filter==='all'||p.country===filter);
  get('filter-count').textContent=`${projects.length} casos visibles. Los indicadores superiores corresponden al registro completo.`;
  get('projects').innerHTML=projects.map(p=>`<article class="panel project" data-project="${esc(p.id)}"><p class="eyebrow">${esc(p.country)} / ${esc(p.category)}</p><h2>${esc(p.name)}</h2><p>${esc(p.location)}</p><p class="project-status">${esc(p.status_label)} <span>· fuente de ${esc(p.status_as_of)}</span></p><p class="sources">${p.status_source_ids.map(sourceLink).join('<br>')}</p><dl class="project-facts"><div><dt>Potencia anunciada</dt><dd>${p.announced_power_mw===null?'No documentada':new Intl.NumberFormat('es-AR').format(p.announced_power_mw)+' MW'}</dd><dd class="fact-note">${esc(p.power_scope)}</dd></div><div><dt>Consumo eléctrico medido</dt><dd>${p.measured_energy_gwh===null?'No documentado':esc(p.measured_energy_gwh)+' GWh · '+esc(p.energy_period)}</dd><dd class="fact-note">Participación de IA: ${p.ai_share_percent===null?'no documentada':esc(p.ai_share_percent)+'%'}. No equivale a cero.</dd></div></dl><h3>Abastecimiento y plazos</h3><p>${esc(p.supply)}</p><p>${esc(p.timeline)}</p><details><summary>Permisos, contexto judicial y próximos documentos</summary><p><b>Permisos:</b> ${esc(p.permits)}</p>${p.legal_events.length?'<ol class="legal-events">'+p.legal_events.map(e=>`<li><b>${esc(e.date)} · ${esc(e.type)}</b><p>${esc(e.description)}</p>${sourceLink(e.source_id)}</li>`).join('')+'</ol>':''}<p>${esc(p.legal_note)}</p><p><b>Evidencia pendiente:</b> ${esc(p.next_evidence)}</p></details></article>`).join('');
 }
 get('country-filter').addEventListener('change',render);render();
})();
