"""Publish descriptive alerts, threshold sensitivity and same-month IPI context.

Pure offline build from archived inputs. Does not select an optimal threshold,
send notifications, modify the Excel, or touch frozen forecasts.
"""
import hashlib
import itertools
import json
from pathlib import Path

if __package__:
    from .analyze_sector_followups import classify, pair
else:
    from analyze_sector_followups import classify, pair

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variant_rules(base):
    variants = []
    for pct, mw, months in itertools.product([5, 10, 15], [2.5, 5, 10], [2, 3, 4]):
        rules = dict(base, watch_yoy_percent=pct, watch_absolute_mw=mw, persistence_months=months)
        variants.append(dict(id=f'w{pct}-m{mw:g}-p{months}', family='grid', rules=rules))
    for field, values in [('priority_yoy_percent', [15, 25]), ('priority_absolute_mw', [5, 15])]:
        for value in values:
            variants.append(dict(id=f'{field}-{value}', family='one_factor', rules=dict(base, **{field:value})))
    return variants


def compact_statuses(rows, period, activities, rules):
    result = {key: [] for key in ['prioridad', 'observar', 'sin_umbral', 'no_evaluable', 'persistent', 'short_history']}
    for a in activities:
        s = classify(rows, period, a['id'], rules)
        result[s['status']].append(a['id'])
        if s.get('persistent'):
            result['persistent'].append(a['id'])
        if not s.get('persistence_evaluable', False):
            result['short_history'].append(a['id'])
    return result


def physical_comparison(history, evidence):
    if evidence['period'] > evidence['published_at'][:7] or evidence['published_at'] > evidence['retrieved_at']:
        raise ValueError('Invalid physical-production availability dates')
    rows = {r['period']: r for r in history['monthly']}
    labels = {a['id']:a['label'] for a in history['activities']}
    comparisons = []
    for source in evidence['observations']:
        key = source['electricity_activity_id']
        observed = pair(rows, evidence['period'], key)
        if observed is None:
            raise ValueError('Cannot compare production against missing or partial electricity month')
        p, e = source['yoy_percent'], observed['yoy_percent']
        direction = 'Ambas caen' if p < 0 and e < 0 else 'Ambas suben' if p > 0 and e > 0 else 'Direcciones distintas o sin cambio'
        comparisons.append(dict(**source, electricity_label=labels[key], electricity_period=evidence['period'],
                                production_period=evidence['period'], electricity_yoy_percent=e,
                                electricity_delta_mw=observed['delta_mw'], direction=direction,
                                causal_inference=False))
    return dict(source=evidence, comparisons=comparisons,
                conclusion='Coincidencia descriptiva de dirección en julio. No demuestra causalidad, elasticidad ni equivalencia de muestras. No confirma las señales eléctricas de agosto.')


def build(history, rules, evidence):
    monthly = {m['period']:m for m in history['monthly']}
    if len(monthly) != len(history['monthly']):
        raise ValueError('Duplicate monthly period')
    periods = [m['period'] for m in history['monthly'] if m['complete_month'] and
               any(pair(monthly, m['period'], a['id']) is not None for a in history['activities'])]
    if not periods:
        raise ValueError('No complete comparable months')
    latest = max(periods)
    baseline = {}
    for p in periods:
        values = []
        for a in history['activities']:
            r = classify(monthly, p, a['id'], rules)
            r.pop('persistence_inputs', None)
            values.append(dict(id=a['id'], **r))
        baseline[p] = dict(rows=values, aluar=classify(monthly, p, 'aluar', rules))
    scenarios = []
    for v in variant_rules(rules):
        states = {p:compact_statuses(monthly, p, history['activities'], v['rules']) for p in periods}
        scenarios.append(dict(**v, periods=states,
            historical_priority_months=sum(len(s['prioridad']) for s in states.values()),
            historical_observe_months=sum(len(s['observar']) for s in states.values()),
            historical_evaluable_activity_months=sum(14-len(s['no_evaluable']) for s in states.values())))
    grid = [s for s in scenarios if s['family']=='grid']
    sensitivity = {}
    for p in periods:
        counts = [len(s['periods'][p]['prioridad']) for s in grid]
        sensitivity[p] = dict(min_priority=min(counts), max_priority=max(counts), scenario_count=len(grid),
            frequency={a['id']:sum(a['id'] in s['periods'][p]['prioridad'] for s in grid) for a in history['activities']})
    return dict(reviewed_at='2026-09-26', latest_period=latest, periods=periods,
                partial_periods=[m['period'] for m in history['monthly'] if not m['complete_month']],
                scope=history['scope'], activities=history['activities'], baseline_rules=rules,
                baseline_scenario_id='w10-m5-p3', baseline=baseline, scenarios=scenarios,
                sensitivity=sensitivity, production=physical_comparison(history, evidence),
                deployment=dict(mode='tablero_descriptivo_exploratorio', notification_enabled=False,
                                automatic_refresh=False, rule_selection='Se conserva proposal-1; ninguna variante se seleccionó como ganadora.'),
                source=history['source'],
                caveat='27 combinaciones y 4 cambios de un solo umbral. Frecuencia de selección no es probabilidad ni confianza estadística. Historia revisada: no validación prospectiva.')


def main():
    paths = ['data/activity_monthly_history.json', 'data/sector_alert_rules.json', 'data/physical_production_evidence.json']
    history, rules, evidence = [json.loads((ROOT/p).read_text()) for p in paths]
    if sha(ROOT/evidence['local_file']) != evidence['sha256']:
        raise ValueError('IPI source archive changed')
    if sha(ROOT/history['source']['archive']) != history['source']['sha256']:
        raise ValueError('Electricity source archive changed')
    result = build(history, rules, evidence)
    result['input_sha256'] = {p:sha(ROOT/p) for p in paths}
    text = json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    (ROOT/'dashboard/sector-alerts-data.js').write_text('window.SECTOR_ALERTS = '+text+';\n')
    (ROOT/'dashboard/downloads/sector_alerts.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    output = ROOT/'reports/research'; output.mkdir(parents=True, exist_ok=True)
    (output/'produccion-y-sensibilidad.md').write_text(report(result))
    print(f'Alerts: {len(result["periods"])} complete comparable months; {len(result["scenarios"])} scenarios; latest {result["latest_period"]}.')
    print(json.dumps(result['sensitivity'][result['latest_period']], ensure_ascii=False))


def report(data):
    latest = data['latest_period']; s = data['sensitivity'][latest]
    fmt = lambda v: f'{v:+.1f}'.replace('.', ',')
    comparisons = '\n'.join(f"| {r['electricity_label']} | {fmt(r['electricity_yoy_percent'])}% | {r['production_label']} | {fmt(r['yoy_percent'])}% | {r['direction']} |" for r in data['production']['comparisons'])
    frequency = '\n'.join(f"| {a['label']} | {s['frequency'][a['id']]}/27 |" for a in data['activities'])
    baseline = next(v for v in data['scenarios'] if v['id']==data['baseline_scenario_id'])
    rows = [baseline]+[v for v in data['scenarios'] if v['family']=='one_factor']
    variants = '\n'.join(f"| {v['rules']['priority_yoy_percent']}% y {v['rules']['priority_absolute_mw']} MW | {len(v['periods'][latest]['prioridad'])} | {v['historical_priority_months']} |" for v in rows)
    return f'''# Alertas, producción y sensibilidad de umbrales

Revisión: 26/09/2026. Las alertas se integran como módulo descriptivo del tablero, sin notificaciones ni actualización automática. La regla base sigue siendo `proposal-1`; los umbrales no se optimizaron para conseguir un resultado deseado.

## Producción: el contraste válido llega a julio

El [IPI manufacturero de julio](https://www.indec.gob.ar/uploads/informesdeprensa/ipi_manufacturero_09_26B810401E77.pdf) fue publicado el 08/09/2026 y consultado el 26/09. Se comparan tasas interanuales de julio en ambas fuentes, no electricidad de agosto con producción de julio.

| Categoría eléctrica | Electricidad julio interanual | Indicador INDEC | IPI julio interanual | Lectura |
| --- | ---: | --- | ---: | --- |
{comparisons}

Cemento es un proxy parcial de la categoría eléctrica de cemento y canteras. Metales no equivale a industrias metálicas básicas. Textiles no incluye aquí prendas de vestir. No hay un panel común validado entre INDEC y CAMMESA. La coincidencia de signo no mide causalidad, intensidad energética ni elasticidades. No promediar índices de volumen con MW.

El IPI combina variables de volumen y otras aproximaciones, incluidas ventas deflactadas; no representa toneladas medidas para todas las ramas (metodología, página 26). Los cuadros usados son 2.3 (página 9), 2.9 (página 15) y 2.11 (página 17). Los valores son provisorios.

La [página oficial](https://www.indec.gob.ar/Nivel4/Tema/3/6/14) anuncia el 07/10/2026 para el informe de agosto. A esta revisión, producción de agosto se mantiene ausente: no se la estima ni se usa julio como sustituto. La captura eléctrica es retrospectiva y revisable.

## Sensibilidad: no existe una única cantidad natural de alertas

Se evaluaron las 27 combinaciones de umbral de observación {{5%, 10%, 15%}}, cambio absoluto {{2,5; 5; 10 MW}} y persistencia {{2, 3, 4 meses}}. La prioridad por magnitud permanece fija en 20% y 10 MW. Para agosto, resultan entre **{s['min_priority']} y {s['max_priority']} actividades prioritarias**, frente a {len(baseline['periods'][latest]['prioridad'])} con la regla base.

| Actividad | Prioridad en combinaciones de la grilla |
| --- | ---: |
{frequency}

El cociente sobre 27 describe dependencia de esos criterios, no una probabilidad, nivel de confianza ni prueba de robustez a otras fuentes. Las actividades que cumplen 20% y 10 MW siempre entran en esta grilla por construcción. Los cuatro escenarios adicionales de abajo examinan precisamente esa regla de magnitud, cambiando un parámetro por vez y dejando observación y persistencia en la base.

| Prioridad por magnitud | Prioritarias en agosto | Actividad-meses prioritarios en historia |
| --- | ---: | ---: |
{variants}

Historia: 44 meses comparables, enero de 2023-agosto de 2026, 14 actividades, 616 actividad-meses. Los conteos repiten actividades persistentes; no son eventos independientes. Aluar queda aparte. Al principio de la historia puede faltar la persistencia requerida. Son resultados retrospectivos sobre una sola captura, no desempeño prospectivo, falsos positivos ni exactitud predictiva.

## Uso en el tablero

El selector de mes mantiene la regla base. El laboratorio de sensibilidad tiene controles separados y un botón para restaurarla; cambiar controles no guarda ni redefine la regla oficial del proyecto. El contraste de producción mantiene su propio período visible. Los estados textuales acompañan el color, las tablas pueden recorrerse con teclado y los originales permanecen intactos.

La calidad de fuente sigue condicionada por cobertura de establecimientos no verificada y la discrepancia PDF-XLSX documentada. Ningún indicador identifica demanda de IA. El Excel descargable y los pronósticos congelados no se modifican en esta ampliación.

Los resultados completos y las huellas de entradas están en la descarga JSON del módulo de alertas. Reproducir: `python3 scripts/build_sector_alerts.py`.
'''


if __name__ == '__main__':
    main()
