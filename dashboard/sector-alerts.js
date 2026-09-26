(() => {
  'use strict';
  const d = window.SECTOR_ALERTS;
  const $ = id => document.getElementById(id);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = (value, signed = false) => value == null ? 'No disponible' : new Intl.NumberFormat('es-AR', {maximumFractionDigits:1, minimumFractionDigits:1, signDisplay:signed?'exceptZero':'auto'}).format(value);
  const month = p => new Intl.DateTimeFormat('es-AR', {month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(p+'-01T00:00:00Z'));
  const statusNames = {prioridad:'Prioridad',observar:'Observar',sin_umbral:'Sin umbral',no_evaluable:'No evaluable'};
  const badge = status => `<span class="status status-${status}">${statusNames[status]}</span>`;
  const scenario = id => d.scenarios.find(s => s.id === id);
  const currentScenario = () => scenario(`w${$('sensitivity-percent').value}-m${$('sensitivity-mw').value}-p${$('sensitivity-months').value}`);
  const state = (s,id) => ['prioridad','observar','sin_umbral','no_evaluable'].find(k => s[k].includes(id));
  const baseScenario = scenario(d.baseline_scenario_id);
  const label = Object.fromEntries(d.activities.map(a => [a.id,a.label]));
  const rank = {prioridad:0,observar:1,sin_umbral:2,no_evaluable:3};
  $('alert-period').innerHTML = [...d.periods].reverse().map(p => `<option value="${p}">${month(p)}</option>`).join('');
  const requested = new URLSearchParams(location.search).get('period');
  $('alert-period').value = d.periods.includes(requested) ? requested : d.latest_period;
  const rules = d.baseline_rules;
  $('base-rules').textContent = `Regla ${rules.version}: observar desde ${rules.watch_yoy_percent}% y ${rules.watch_absolute_mw} MW en valor absoluto. Prioridad desde ${rules.priority_yoy_percent}% y ${rules.priority_absolute_mw} MW, o al cumplir la observación durante ${rules.persistence_months} meses en la misma dirección.`;

  function renderSensitivity() {
    const p = $('alert-period').value, selected = currentScenario(), base = baseScenario.periods[p], alt = selected.periods[p], sensitivity = d.sensitivity[p];
    const changed = d.activities.filter(a => state(base,a.id) !== state(alt,a.id)).length;
    $('sensitivity-summary').textContent = `${month(p)}: ${alt.prioridad.length} actividades prioritarias con la variante elegida; ${base.prioridad.length} con la base. Cambian ${changed} estados. En las 27 combinaciones: entre ${sensitivity.min_priority} y ${sensitivity.max_priority} prioritarias.`;
    $('scenario-label').textContent = selected.id === d.baseline_scenario_id ? 'Controles en la regla base.' : 'Variante exploratoria: la regla base no se modificó.';
    $('scenario-label').className = 'selected-rule';
    $('sensitivity-caption').textContent = `${month(p)} · misma fuente y período; solo cambian reglas editoriales`;
    $('sensitivity-rows').innerHTML = d.activities.map(a => `<tr><th scope="row">${esc(a.label)}</th><td>${badge(state(base,a.id))}</td><td>${badge(state(alt,a.id))}</td><td>${sensitivity.frequency[a.id]} de 27</td></tr>`).join('');
    $('priority-caption').textContent = `Prioridad por magnitud · ${month(p)} y conteos retrospectivos sobre 616 actividad-meses`;
    $('priority-rows').innerHTML = [baseScenario,...d.scenarios.filter(s=>s.family==='one_factor')].map(s=>`<tr><th scope="row">${s.rules.priority_yoy_percent}% y ${s.rules.priority_absolute_mw} MW${s.id===d.baseline_scenario_id?' · base':''}</th><td>${s.periods[p].prioridad.length}</td><td>${s.historical_priority_months}</td></tr>`).join('');
  }

  function renderMonth() {
    const p = $('alert-period').value, b = d.baseline[p], counts = baseScenario.periods[p];
    $('alert-summary').textContent = `${month(p)}: ${counts.prioridad.length} actividades en prioridad y ${counts.observar.length} en observación, de 14. Aluar se evalúa aparte.`;
    $('alert-caption').textContent = `${month(p)} contra el mismo mes del año anterior · MW medios · regla base`;
    const rows = [...b.rows].sort((a,b)=>rank[a.status]-rank[b.status] || Math.abs(b.delta_mw??0)-Math.abs(a.delta_mw??0));
    $('alert-rows').innerHTML = rows.map(r=>{
      const magnitude = r.yoy_percent != null && Math.abs(r.yoy_percent)+1e-9 >= rules.priority_yoy_percent && Math.abs(r.delta_mw)+1e-9 >= rules.priority_absolute_mw;
      const reasons = [];
      if (magnitude) reasons.push('Magnitud');
      if (r.persistent) reasons.push('Persistencia de 3 meses');
      if (!r.persistence_evaluable) reasons.push('Historia insuficiente para persistencia');
      if (!reasons.length) reasons.push(r.status==='observar'?'Cambio relevante del mes':'No cumple los límites');
      return `<tr><th scope="row">${esc(label[r.id])}</th><td>${number(r.yoy_percent,true)}${r.yoy_percent==null?'':'%'}</td><td>${number(r.delta_mw,true)}</td><td>${badge(r.status)}</td><td>${reasons.join(' · ')}</td></tr>`;
    }).join('');
    const wd = b.rows.find(r=>r.working_day_difference!=null);
    $('calendar-note').textContent = wd ? `Diferencia de días hábiles frente al mismo mes anterior: ${number(wd.working_day_difference,true)}. ${wd.calendar_review?'Revisar calendario: se alcanza el límite de dos días. ':''}No se ajustó por días hábiles ni clima.` : 'Calendario no evaluable para este período.';
    const al = b.aluar;
    $('alert-aluar').textContent = `${month(p)}: ${number(al.yoy_percent,true)}% interanual, cambio de ${number(al.delta_mw,true)} MW. Estado: ${statusNames[al.status]}.`;
    renderSensitivity();
  }

  $('production-rows').innerHTML = d.production.comparisons.map(r=>`<tr><th scope="row">${esc(r.electricity_label)}</th><td>${number(r.electricity_yoy_percent,true)}%</td><td>${esc(r.production_label)}</td><td>${number(r.yoy_percent,true)}%</td><td>${esc(r.direction)}</td></tr>`).join('');
  $('production-finding').textContent = d.production.conclusion;
  $('production-mapping').innerHTML = d.production.comparisons.map(r=>`<li><b>${esc(r.production_label)}:</b> ${esc(r.mapping)} Cuadro ${esc(r.table)}, página ${r.page}.</li>`).join('');
  const source = d.production.source;
  $('production-source').innerHTML = `INDEC · publicación ${esc(source.published_at)} · consulta ${esc(source.retrieved_at)}. <a href="${esc(source.source_url)}" target="_blank" rel="noopener">Abrir informe oficial de julio ↗</a> · <a href="${esc(source.landing_url)}" target="_blank" rel="noopener">Publicaciones y próxima fecha ↗</a>`;
  $('alert-sources').innerHTML = `<p><a href="${esc(d.source.url)}" target="_blank" rel="noopener">CAMMESA, base diaria oficial ↗</a>. Captura ${esc(d.source.retrieved_at)}. Hoja ${esc(d.source.sheet)}. El enlace puede actualizarse; la huella identifica la copia utilizada.</p><pre>SHA-256 CAMMESA: ${esc(d.source.sha256)}\nSHA-256 INDEC IPI: ${esc(source.sha256)}</pre><p>El JSON incluye los parámetros, 31 escenarios, 44 meses comparables, el mapeo de categorías y las huellas de los archivos de entrada. No se calcula una participación de IA.</p>`;
  $('alert-period').addEventListener('change',renderMonth);
  for (const id of ['sensitivity-percent','sensitivity-mw','sensitivity-months']) $(id).addEventListener('change',renderSensitivity);
  $('reset-thresholds').addEventListener('click',()=>{
    $('sensitivity-percent').value=String(rules.watch_yoy_percent);
    $('sensitivity-mw').value=String(rules.watch_absolute_mw);
    $('sensitivity-months').value=String(rules.persistence_months);
    renderSensitivity();
  });
  renderMonth();
})();
