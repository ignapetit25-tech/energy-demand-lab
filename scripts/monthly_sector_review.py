"""Date-aligned descriptive additions, separate from prospective evaluation."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    def read(p):return json.loads((ROOT/p).read_text())
    return dict(alerts=read('dashboard/downloads/sector_alerts.json'),
                production=read('data/production_history.json'),
                registry=read('dashboard/downloads/sector_prospective_registry.json'),
                metals=read('reports/research/divergencias-metales.json'))


def review(period,data):
    p=period[:7];a=data['alerts'];h=data['production'];g=data['registry']
    labels={v['id']:v['label'] for v in a['activities']}
    rows=[dict(r,label=labels[r['id']]) for r in a['baseline'].get(p,{}).get('rows',[])]
    # Never substitute another month's IPI for the selected month.
    comparisons=[dict(r,label=next(v['production_label'] for v in h['mapping'] if v['electricity_activity_id']==r['activity_id'])) for r in h['comparisons'] if r['period']==p]
    return dict(period=p,rows=rows,production=comparisons,
        alert_note=(f'{sum(r["status"]=="prioridad" for r in rows)} prioridades entre {len(rows)} actividades en {p}. Regla propuesta, reconstrucción histórica; no señal emitida en aquella fecha.' if rows else 'Sin alertas reconstruidas para este mes.'),
        production_note=(f'Contraste del mismo mes: {p}. Categorías relacionadas, sin panel común validado.' if comparisons else f'Sin contraste IPI del mes {p} en esta captura. Historia disponible: {h["periods"][0]} a {h["periods"][-1]}; no se traslada julio a agosto.'),
        registry_note=f'Registro prospectivo actual, independiente del mes seleccionado: {g["window"][0]} a {g["window"][1]}. {g["issued_months"]} meses emitidos, {g["outcome_months"]} con resultado; {g["eligible_pairs"]} pares elegibles. Decisión: {g["decision"]}. Actualización manual, sin notificaciones.',
        scope=a['scope'])


def markdown_section(r):
    v=r.get('sector_review')
    if not v:return []
    rate=lambda n:f'{n:+.2f}%'.replace('.',',')
    lines=['','## Alertas y producción: mes seleccionado','',v['alert_note'],'',v['scope'],'']
    if v['rows']:
        lines+=['| Actividad | Electricidad interanual | Estado |','| --- | ---: | --- |']
        lines += [f'| {x["label"]} | {rate(x["yoy_percent"])} | {x["status"]} |' for x in v['rows']]
        lines+=['','La persistencia necesita tres comparaciones completas: enero y febrero de 2023 tienen historia insuficiente para ese criterio. No se interpreta ausencia de umbral como ausencia de riesgo.']
    lines+=['',v['production_note'],'']
    if v['production']:
        lines+=['| Categoría relacionada | Electricidad % | IPI % |','| --- | ---: | ---: |']
        lines += [f'| {x["label"]} | {rate(x["electricity_yoy_percent"])} | {rate(x["yoy_percent"])} |' for x in v['production']]
    lines+=['','Fuentes y correspondencias: https://ignapetit25-tech.github.io/energy-demand-lab/sector-alerts.html#production',
            '', '## Registro prospectivo: estado actual','',v['registry_note'],
            'Sin resultados elegibles, las métricas permanecen no disponibles: no son cero ni evidencia de éxito.',
            'Registro y huellas: https://ignapetit25-tech.github.io/energy-demand-lab/downloads/sector_prospective_registry.json']
    return lines
