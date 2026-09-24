'use strict';
(()=>{
 const r=window.RESEARCH_DATA.registry,get=id=>document.getElementById(id);
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const num=v=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:2}).format(v);
 const sources=Object.fromEntries(r.sources.map(s=>[s.id,s]));
 const sourceLink=id=>{const s=sources[id];return '<a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.publisher)+' · '+esc(s.date||'consulta '+s.retrieved_at) +' ↗</a> <span class="source-kind">('+esc(s.type)+')</span>';};
 const ar=r.projects.filter(p=>p.country==='Argentina');
 get('registry-date').textContent=r.reviewed_at;get('registry-scope').textContent=r.scope;get('registry-rules').textContent=r.rules;
 get('project-count').textContent=r.projects.length;get('argentina-count').textContent=ar.length;
 get('meter-count').textContent=ar.filter(p=>p.technical_facts.some(f=>['MW','kW'].includes(f.unit))).length+' de '+ar.length;
 get('argentina-overview').innerHTML=ar.map(p=>'<tr><th scope="row"><a href="#'+esc(p.id)+'">'+esc(p.name)+'</a></th><td>'+esc(p.power_summary)+'</td><td>'+esc(p.ai_relation)+'</td></tr>').join('');
 function render(){
  const filter=get('country-filter').value,projects=r.projects.filter(p=>filter==='all'||p.country===filter);
  get('filter-count').textContent=projects.length+' casos visibles. Los indicadores superiores distinguen registro completo y foco argentino.';
  get('projects').innerHTML=projects.map(p=>{
   const facts=p.technical_facts.length?'<div class="technical-grid">'+p.technical_facts.map(f=>'<div class="technical-card"><p class="eyebrow">'+esc(f.label)+'</p><p class="technical-value">'+esc(f.qualifier)+' '+num(f.value)+' <small>'+esc(f.unit)+'</small></p><p>'+esc(f.note)+'</p><p class="sources">'+sourceLink(f.source_id)+'</p></div>').join('')+'</div>':'<p><b>Potencia anunciada:</b> '+(p.announced_power_mw===null?'No documentada':num(p.announced_power_mw)+' MW')+'. '+esc(p.power_scope)+'</p>';
   const legal=p.legal_events.length?'<ol class="legal-events">'+p.legal_events.map(e=>'<li><b>'+esc(e.date)+' · '+esc(e.type)+'</b><p>'+esc(e.description)+'</p>'+sourceLink(e.source_id)+'</li>').join('')+'</ol>':'';
   return '<article class="panel project" id="'+esc(p.id)+'" data-project="'+esc(p.id)+'"><p class="eyebrow">'+esc(p.country)+' / '+esc(p.category)+'</p><h2>'+esc(p.name)+'</h2><p>'+esc(p.location)+'</p><p class="project-status">'+esc(p.status_label)+' <span>· referencia de '+esc(p.status_as_of)+'</span></p><p class="sources">'+p.status_source_ids.map(sourceLink).join('<br>')+'</p>'+facts+'<p class="ai-relation"><b>Relación con IA:</b> '+esc(p.ai_relation)+'</p><h3>Abastecimiento y plazos</h3><p>'+esc(p.supply)+'</p><p>'+esc(p.timeline)+'</p><details><summary>Consumo medido, permisos y evidencia pendiente</summary><p><b>Energía en GWh:</b> '+(p.measured_energy_gwh===null?'no documentada con período en las fuentes incorporadas':num(p.measured_energy_gwh)+' · '+esc(p.energy_period))+'. <b>Participación de IA:</b> '+(p.ai_share_percent===null?'no documentada':num(p.ai_share_percent)+'%')+'. No equivale a cero.</p><p><b>Permisos:</b> '+esc(p.permits)+'</p>'+legal+'<p>'+esc(p.legal_note)+'</p><p><b>Evidencia pendiente:</b> '+esc(p.next_evidence)+'</p></details></article>';
  }).join('');
 }
 get('country-filter').addEventListener('change',render);
 get('argentina-overview').addEventListener('click',()=>{get('country-filter').value='Argentina';render();});
 render();
})();
