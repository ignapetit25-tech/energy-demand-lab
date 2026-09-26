"""Decision support from archived evidence, not an automatic data refresh."""
import json
from datetime import date,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(p):return json.loads((ROOT/p).read_text())


def operational_check(registry,last_complete,today):
    unresolved=next((m for m in registry['months'] if m['status'] not in ['registrado','excluido_documentado']),None)
    if not unresolved:return dict(period=None,state='Cohorte registrada',steps=['Revisar elegibilidad y cierre según el protocolo.'],automatic=False)
    p=unresolved['period'];y,m=map(int,p.split('-'));close=date(y+int(m==12),m%12+1,1)
    steps=[]
    if today<close:steps.append(f'Esperar el cierre de {p}. Primera fecha posible de captura completa: {close.isoformat()}; no es una fecha oficial de publicación.')
    if last_complete<p:steps.append(f'Falta una captura eléctrica completa de {p}; la instantánea disponible cierra en {last_complete}.')
    if not unresolved['issued']:
        steps+=['Verificar la última publicación IPI conocida y archivar el comparador con revisión humana.',
                'Emitir una sola vez con sector_registry issue; publicar originales y comprobar el commit antes del IPI objetivo.']
    else:steps+=['Comprobar que la emisión tenga verificación pública anterior al IPI objetivo.',
                 'Registrar la primera observación capturada del IPI objetivo; conservar revisiones por separado.']
    steps+=['Si se perdió la oportunidad, documentar la exclusión; no retrofechar.', 'Revisar, ejecutar las pruebas y publicar los cambios manualmente.']
    return dict(period=p,state='Aún no corresponde emitir' if today<close else 'Revisión manual requerida',steps=steps,automatic=False)


def build(data,today=None):
    today=today or datetime.now(timezone.utc).date()
    n=load('data/sector_source_manifest.json');a=load('data/activity_monthly_history.json');p=data['production'];m=data['metals']
    complete=[r['period'] for r in a['monthly'] if r['complete_month']]
    partial=[r['period'] for r in a['monthly'] if not r['complete_month']]
    def item(id,label,period,captured,published,source,sha,coverage,condition,next_check):
        return dict(id=id,label=label,latest_period=period,captured_at=captured,published_at=published,source_url=source,sha256=sha,coverage=coverage,condition=condition,next_check=next_check)
    sources=[item('national','Demanda nacional',n['coverage']['end'][:7],n['downloaded_at'],None,n['api_query'],n['sha256'],f"{n['coverage']['observations']} meses; tres sectores y total",'Instantánea histórica; publicación original no verificada','Comprobar nueva edición de la fuente antes de actualizar el informe.'),
      item('electricity','Actividades eléctricas',complete[-1],a['source']['retrieved_at'],None,a['source']['url'],a['source']['sha256'],f"{len(complete)} meses completos; 14 actividades y Aluar separado",'Provisorio; panel de usuarios no constante garantizado','Capturar el próximo mes completo y revisar cambios de cobertura.'),
      item('production','Producción IPI',p['periods'][-1],p['source']['retrieved_at'],p['source']['publication_date'],p['source']['url'],p['source']['sha256'],f"{len(p['periods'])} meses comparables; tres categorías relacionadas",'Serie revisada; fecha propia del XLS no verificada','Verificar nueva publicación INDEC y preservar la edición anterior.')]
    source_map={s['id']:s for s in m['sources']}
    source_map.update(electricity_source=m['electricity_source'],production_source=m['production_source'])
    case=load('data/metals_casebook.json')
    for h in case['hypotheses']:h['source_url']=source_map[h['source']]['url']
    s=m['summary']
    narrative=f"Revisión {m['reviewed_at']}, independiente del mes seleccionado: {s['opposite']} de {s['pairs']} meses muestran signos opuestos; {s['material_opposite']} fuera de ±0,5%. La oposición persiste en {s['opposite_after_median']} usando mediana diaria y en {s['opposite_after_working_mean']} usando media de días hábiles. La causa no está identificada."
    return dict(as_of=today.isoformat(),snapshot_note='Estado de archivos conservados, no comprobación en vivo de las fuentes. Las próximas comprobaciones son tareas propuestas, no un calendario oficial.',sources=sources,partial_periods=partial,
                metals=dict(narrative=narrative,summary=s,casebook=case,april_case=m['april_case'],sources=m['sources']),
                operations=operational_check(data['registry'],complete[-1],today),
                document_assistant=dict(status='Preparación y evaluación local; sin modelo conectado',measured_accuracy=None,real_runs=0,description='Paquete de extracción con fuentes y evaluación contra referencias revisadas. No se envían documentos ni se incorporan respuestas automáticamente.'))


def executive(report,review):
    comparisons={r['activity_id']:r for r in review['production']}
    focus=sorted((r for r in review['rows'] if r['status']=='prioridad'),key=lambda r:(-abs(r['delta_mw']),r['id']))[:3]
    findings=[]
    for r in focus:
        c=comparisons.get(r['id'])
        quality=r['quality']
        action=('Investigar oposición de signos; revisar cobertura y composición.' if not c['direction_match'] else 'Comprobar cobertura y persistencia; coincidencia no implica causalidad.') if c else ('Verificar la publicación IPI del mismo mes; no sustituir por el mes anterior.' if r['id'] in ['construction','metals','textiles'] else 'Buscar una medición de producción con cobertura comparable.')
        findings.append(dict(id=r['id'],label=r['label'],yoy_percent=r['yoy_percent'],delta_mw=r['delta_mw'],intensity=r['status'],persistent=r['persistent'] if r.get('persistence_evaluable') else None,quality=quality,action=action))
    return dict(summary=report['summary'],findings=findings,ordering='Hasta tres prioridades, ordenadas por magnitud absoluta del cambio en MW dentro de la muestra; no por riesgo económico ni confianza estadística.',
                boundary='Las señales organizan investigación. No estiman causas, consumo de IA ni probabilidad de recesión.',
                next_action='Revisar las prioridades y sus límites antes de interpretar el movimiento.' if findings else 'No hay señales de prioridad bajo esta regla; no equivale a ausencia de riesgo.' if review['rows'] else 'No hay prioridades disponibles para este mes; revisar cobertura e historia antes de interpretar ausencia de señales.')


def text_section(executive,workbench):
    lines=['','## Resumen ejecutivo: qué revisar primero','',executive['ordering']]
    for f in executive['findings']:
        rate=f"{f['yoy_percent']:+.2f}".replace('.',',');mw=f"{f['delta_mw']:+.2f}".replace('.',',')
        persistence='no evaluable' if f['persistent'] is None else 'sí' if f['persistent'] else 'no'
        lines += [f"- {f['label']}: {rate}%, {mw} MW; intensidad: {f['intensity']}; persistencia: {persistence}. Calidad: {f['quality']}. Acción: {f['action']}"]
    lines += [executive['next_action'],executive['boundary'],'','## Calidad y actualización: instantánea actual','',workbench['snapshot_note']]
    for s in workbench['sources']:lines += [f"- {s['label']}: último período completo {s['latest_period']}; captura {s['captured_at']}; publicación {s['published_at'] or 'no verificada'}. {s['condition']}. Próxima comprobación: {s['next_check']}"]
    lines += ['','## Expediente actual de metales','',workbench['metals']['narrative']]
    for h in workbench['metals']['casebook']['hypotheses']:lines += [f"- {h['title']} — {h['status']}. A favor: {h['support']} Límite o evidencia contraria: {h['counter']} Dato decisivo: {h['needed']} Acción: {h['action']} Fuente: {h['source_url']}"]
    lines += ['','## Operación prospectiva: preparación, no emisión','',workbench['operations']['state']]+['- '+x for x in workbench['operations']['steps']]
    lines += ['','Asistencia documental: paquete y evaluador local disponibles. Sin modelo conectado ni exactitud medida.','Guía: https://github.com/ignapetit25-tech/energy-demand-lab/blob/main/docs/mesa-de-analisis.md','']
    return lines


if __name__=='__main__':
    from scripts.monthly_sector_review import inputs
    print(json.dumps(build(inputs())['operations'],ensure_ascii=False,indent=2))
