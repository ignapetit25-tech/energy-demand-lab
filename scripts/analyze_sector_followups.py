"""Read archived sources, audit discrepancies and illustrate proposed alert rules.

Never changes the CAMMESA workbook, published history, Excel, or forecasts.
"""
import hashlib
import io
import json
import math
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

if __package__:
    from .build_activity_history import extract, summarize, SOURCE, SHA, NS
else:
    from build_activity_history import extract, summarize, SOURCE, SHA, NS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/research'
PDFS = {
    '2026-09-17': ('data/reference/cammesa-gumas-2026-09-17.pdf', 'a681b72a0d000be76d17ea21826037f96c8d20859c89b68a877f7476513f49ff'),
    '2026-09-24': ('data/reference/cammesa-gumas-2026-09-24.pdf', '471a3c0bf65b8156d8dfd367544a25e0fa85911497031013d41733486274e189'),
}
PDF_KEYS = ['food_commerce_services', 'ports', 'commerce', 'food', 'public_services',
            'aluar', 'industry', 'automotive', 'petroleum_products', 'construction',
            'wood_paper', 'metals', 'steel', 'textiles', 'chemicals', 'oil_minerals',
            'mining', 'oil_extraction', 'total', 'without_aluar']
LABEL_STARTS = ['ALIMENTACIÓN,', 'CARGAS Y', 'COMERCIO Y', 'INDUSTRIA DE LA ALIMENTACIÓN',
                'SECTOR DE SERVICIOS', 'ALUAR', 'INDUSTRIAS', 'INDUSTRIA AUTOMOTRIZ',
                'INDUSTRIA DE DERIVADOS', 'INDUSTRIA DE LA CONSTRUCCIÓN', 'INDUSTRIA DE LA MADERA',
                'INDUSTRIA DE PRODUCTOS', 'GRAN SIDERURGIA', 'INDUSTRIA TEXTIL',
                'INDUSTRIAS QUÍMICAS', 'PETROLEOS Y', 'EXTRACCIÓN DE MINERALES',
                'EXTRACCIÓN DE PETRÓLEO', 'TOTAL', 'TOTAL SIN ALUAR']


def pdf_table(path, expected_hash):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError('PDF archive changed')
    text = subprocess.check_output(['pdftotext', '-f', '7', '-l', '7', '-layout', str(path), '-'], text=True)
    pattern = r'^\s*(.*?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)%\s+(-?\d+\.\d+)%\s*$'
    rows = [m.groups() for line in text.splitlines() if (m := re.match(pattern, line))]
    if len(rows) != len(PDF_KEYS):
        raise ValueError('Unexpected PDF table shape')
    for row, label in zip(rows, LABEL_STARTS):
        if not row[0].startswith(label):
            raise ValueError('Unexpected PDF row order')
    return {key: {'label': row[0], 'september_2025': float(row[1]),
                  'august_2026': float(row[2]), 'september_2026_partial': float(row[3])}
            for key, row in zip(PDF_KEYS, rows)}


def other_sheet_check(daily):
    """Independent cached-value reading of the other two daily source sheets."""
    with ZipFile(ROOT / SOURCE) as outer:
        content = outer.read('Base de datos GU Semanal.xlsx')
    lookup = {r['date']: r for r in daily}
    checks = []
    with ZipFile(io.BytesIO(content)) as z:
        strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        book = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for name, first, mapping in [
            ('Base diaria', 14, {'total': 'I', 'food_commerce_services': 'M', 'industry': 'N', 'oil_minerals': 'O', 'aluar': 'P'}),
            ('Base Detalle diaria GUMAS Rama', 17, {'total': 'L', 'food_commerce_services': 'H', 'industry': 'I', 'oil_minerals': 'J', 'aluar': 'K'}),
        ]:
            sh = next(s for s in book.find('s:sheets', NS) if s.attrib['name'] == name)
            target = rels[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            xml = ET.fromstring(z.read(target.lstrip('/') if target.startswith('/') else 'xl/' + target))
            n, maximum, seen, august = 0, 0, set(), []
            for row in xml.findall('s:sheetData/s:row', NS):
                if int(row.attrib['r']) < first:
                    continue
                cells = {re.sub('[0-9]', '', c.attrib['r']): c for c in row}
                def value(col):
                    c = cells.get(col)
                    if c is None or c.find('s:v', NS) is None:
                        return None
                    v = c.find('s:v', NS).text
                    return strings[int(v)] if c.attrib.get('t') == 's' else float(v)
                if value('D') is None:
                    continue
                month = datetime(1899, 12, 30) + timedelta(days=value('D'))
                day = month.replace(day=int(value('E'))).date().isoformat()
                if day in seen or day not in lookup:
                    raise ValueError('Source sheet date mismatch')
                seen.add(day)
                values = {key: value(col) for key, col in mapping.items()}
                maximum = max(maximum, *(abs(v - lookup[day]['mw'][k]) for k, v in values.items()))
                if day.startswith('2026-08'):
                    august.append(values['total'])
                n += 1
            if seen != set(lookup):
                raise ValueError('Source sheet coverage mismatch')
            checks.append(dict(sheet=name, daily_count=n, maximum_absolute_difference_mw=maximum,
                               august_total_mw=sum(august)/len(august)))
    return checks


def discrepancies(daily, monthly):
    tables = {edition: pdf_table(ROOT/path, sha) for edition, (path, sha) in PDFS.items()}
    august = next(r for r in monthly if r['period'] == '2026-08')
    rows = []
    for key in PDF_KEYS:
        calculated = august['mw'][key] if key != 'without_aluar' else august['mw']['total'] - august['mw']['aluar']
        before, after = (tables[e][key]['august_2026'] for e in PDFS)
        rows.append(dict(id=key, label=tables['2026-09-24'][key]['label'], pdf17_mw=before,
                         pdf24_mw=after, daily_mean_mw=calculated, pdf_revision_mw=after-before,
                         pdf24_minus_daily_mw=after-calculated,
                         exceeds_single_value_rounding=abs(after-calculated) > .05000001))
    august_days = [r for r in daily if r['date'].startswith('2026-08')]
    variants = []
    for label, rs in [('todos', august_days), ('habiles', [r for r in august_days if r['working_day']]),
                      ('no_habiles', [r for r in august_days if not r['working_day']])]:
        variants.append(dict(days_type=label, count=len(rs), total_mw=sum(r['mw']['total'] for r in rs)/len(rs)))
    return dict(reviewed_at='2026-09-26', period='2026-08', rows=rows, calendar_checks=variants,
                cross_sheet_checks=other_sheet_check(daily),
                source_zip=dict(path=SOURCE, sha256=SHA),
                pdf_sources=[dict(edition=e, path=p, sha256=h, page=7) for e, (p,h) in PDFS.items()],
                rounding_max_mw_for_15_components_plus_total=16*.05,
                cause_status='No confirmada. Cambios de versión observados; revisión de datos operativos plausible, no demostrada para esta diferencia.',
                note='No se modifica ni se empalma ninguna fuente. Los cambios de septiembre 16 a 23 días no son revisiones de un período idéntico.')


def shift(period, offset):
    y, m = map(int, period.split('-'))
    k = y*12 + m - 1 + offset
    return f'{k//12:04d}-{k%12+1:02d}'


def pair(rows, period, key):
    now, old = rows.get(period), rows.get(shift(period, -12))
    if not now or not old or not now['complete_month'] or not old['complete_month']:
        return None
    a, b = now['mw'].get(key), old['mw'].get(key)
    if a is None or b is None or not math.isfinite(a) or not math.isfinite(b) or b <= 0 or a < 0:
        return None
    return dict(delta_mw=a-b, yoy_percent=100*(a/b-1), current_mw=a, previous_mw=b,
                working_day_difference=now['working_days']-old['working_days'])


def classify(rows, period, key, rules):
    values = [pair(rows, shift(period, -i), key) for i in range(rules['persistence_months'])]
    p = values[0]
    if p is None:
        return dict(status='no_evaluable', direction=None, persistent=None, yoy_percent=None, delta_mw=None)
    def at_least(value, threshold):
        # Inclusive boundaries despite floating-point representation, not rounding for display.
        return value >= threshold or math.isclose(value, threshold, rel_tol=0, abs_tol=1e-9)
    def watch(v):
        return v is not None and at_least(abs(v['yoy_percent']), rules['watch_yoy_percent']) and at_least(abs(v['delta_mw']), rules['watch_absolute_mw'])
    sign = 1 if p['delta_mw'] > 0 else -1 if p['delta_mw'] < 0 else 0
    persistent = all(v is not None for v in values) and all(watch(v) and v['delta_mw']*sign > 0 for v in values)
    priority = at_least(abs(p['yoy_percent']), rules['priority_yoy_percent']) and at_least(abs(p['delta_mw']), rules['priority_absolute_mw'])
    status = 'prioridad' if priority or persistent else 'observar' if watch(p) else 'sin_umbral'
    return dict(**p, status=status, direction='suba' if sign > 0 else 'baja' if sign < 0 else 'sin_cambio',
                persistent=persistent, persistence_evaluable=all(v is not None for v in values),
                persistence_inputs=[dict(period=shift(period, -i), comparison=v) for i, v in enumerate(values)],
                calendar_review=abs(p['working_day_difference']) >= rules['calendar_working_day_difference'])


def alert_report(monthly, labels, rules):
    rows = {r['period']: r for r in monthly}
    period = max(r['period'] for r in monthly if r['complete_month'])
    results = [dict(id=a['id'], label=a['label'], **classify(rows, period, a['id'], rules)) for a in labels]
    for r in results:
        branch = next(a['branch'] for a in labels if a['id'] == r['id'])
        denominator = rows[shift(period, -12)]['mw'][branch]
        r['branch'] = branch
        r['branch_contribution_pp'] = 100*r['delta_mw']/denominator if denominator > 0 and r['delta_mw'] is not None else None
    results.sort(key=lambda r: (dict(prioridad=0, observar=1, sin_umbral=2, no_evaluable=3)[r['status']], -abs(r['delta_mw'] or 0)))
    return dict(reviewed_at='2026-09-26', period=period, rules=rules,
                source_sha256=SHA, rows=results,
                aluar=dict(label='Aluar, toma neta de red', **classify(rows, period, 'aluar', rules)),
                data_quality='Cálculos sobre una instantánea revisable. Cobertura de establecimientos no verificada; no confirma cambios de producción.',
                partial_periods=[r['period'] for r in monthly if not r['complete_month']],
                excluded_month_status='no_evaluable', deployment_status='Propuesta ilustrada con datos conocidos. Sin automatización ni alertas enviadas.')


def num(x, digits=2):
    return f'{x:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def write_reports(d, a):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in [('discrepancias-cammesa', d), ('alertas-sectoriales', a)]:
        (OUT / f'{name}.json').write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    table = '\n'.join(f"| {r['label']} | {num(r['pdf17_mw'],1)} | {num(r['pdf24_mw'],1)} | {num(r['daily_mean_mw'],4)} | {num(r['pdf24_minus_daily_mw'],4)} |" for r in d['rows'])
    text = f'''# Discrepancias de CAMMESA: agosto de 2026

Revisión: 26/09/2026. Unidad: MW medios. Se comparan los mismos 31 días de agosto. Los PDF se revisaron en su página 7; las cifras de la base son cálculos propios sobre datos diarios, no transacciones definitivas.

## Resultado

El total pasa de 2.293,1 a 2.295,2 MW entre PDF: +2,1 MW de cambio documental del mismo mes. La base diaria da 2.292,0401 MW. La distancia del PDF del 24/09 frente a la base es 3,1599 MW, aproximadamente 0,138% de la base. No se confirma cuál valor es definitivo ni la causa exacta de la divergencia.

| Actividad o subtotal | PDF 17/09 | PDF 24/09 | Base diaria | PDF 24/09 menos base |
| --- | ---: | ---: | ---: | ---: |
{table}

No sumar filas de actividades junto con sus subtotales. Las diferencias están calculadas contra valores redondeados del PDF; no implican esa precisión en la fuente.

## Explicaciones contrastadas

- **Error de suma o distinta hoja diaria:** se cotejaron las tres hojas diarias por fecha y rama, con 1.727 fechas cada una. La diferencia máxima es inferior a 0,000001 MW; el total de agosto coincide. La conciliación interna no prueba exactitud de las mediciones originales.
- **Días hábiles:** los 20 días marcados hábiles dan 2.363,2214 MW; los 11 no hábiles, 2.162,6197 MW. Ninguno reproduce 2.295,2 MW. El resumen superior del XLSX está configurado para hábiles, pero esta convención no explica la brecha de la tabla mensual del PDF, que declara 31 días.
- **Redondeo:** un total presentado con un decimal admite ±0,05 MW si comparte la misma base. Incluso sumar 15 componentes redondeados y redondear el total daría una cota conservadora de 0,8 MW. La diferencia de 3,1599 MW supera ambas cotas. No basta el redondeo decimal ordinario como única explicación.
- **Revisión de la fuente:** hay cambios verificables entre PDF de igual período. Alimentos sube 0,8 MW, químicas 0,6 MW, extracción de petróleo 0,6 MW y madera/papel 0,1 MW entre las dos ediciones; explican los 2,1 MW publicados. Esto acredita cambios entre versiones, no su causa operativa.
- **Foco de la diferencia PDF-base:** alimentos y extracción de petróleo concentran la mayor parte del saldo. Aluar está dentro del margen de redondeo de un decimal. No hay evidencia en esta comparación de que Aluar origine la discrepancia total.

## Lo que falta para cerrarla

CAMMESA explica que los datos operativos son provisorios y se ajustan antes de consolidarse con el DTE. Eso hace plausible una diferencia de revisión o de corte, pero no identifica qué registros cambiaron aquí. También quedan abiertas diferencias de cobertura, actualización de tablas o de medición. Se necesita el archivo que alimentó cada PDF, su fecha/hora de corte y una conciliación con el DTE. No se atribuye responsabilidad ni se corrigen originales sin esa evidencia.

Las columnas de septiembre de estos PDF cubren 16 y 23 días: no se interpretan sus diferencias como revisiones del mismo período. La afirmación de este informe se restringe a agosto.

## Fuentes y reproducción

- [Publicación y metodología oficial](https://cammesaweb.cammesa.com/2026/09/25/covid-19-comportamiento-de-la-demanda-de-energia-electrica-en-el-mem/), consultada el 26/09/2026.
- [Base diaria oficial](https://cammesaweb.cammesa.com/download/base-de-datos-2/?wpdmdl=39428), captura archivada del 26/09/2026. Este enlace puede cambiar de versión.
- [PDF 17/09 archivado](../../data/reference/cammesa-gumas-2026-09-17.pdf), página 7.
- [PDF 24/09 archivado](../../data/reference/cammesa-gumas-2026-09-24.pdf), página 7.
- [Resultados y hashes](discrepancias-cammesa.json). Reproducir con `python3 scripts/analyze_sector_followups.py` desde el repositorio; requiere `pdftotext`.

No se alteraron el Excel descargable, las fuentes publicadas ni los pronósticos congelados. La [solicitud preparada](../../docs/solicitudes-datos-aluar-cammesa.md) contiene las preguntas pendientes.
'''
    (OUT/'discrepancias-cammesa.md').write_text(text)
    rows = '\n'.join(f"| {r['label']} | {num(r['yoy_percent'],1)}% | {num(r['delta_mw'],1)} | {r['status']} | {'Sí' if r['persistent'] else 'No'} |" for r in a['rows'])
    al = a['aluar']
    (OUT/'alertas-sectoriales.md').write_text(f'''# Propuesta de alertas: aplicación a agosto de 2026

Fecha de diseño: 26/09/2026. Estado: propuesta exploratoria, no desplegada. No se enviaron alertas ni se programó un monitor. [Reglas y procedimiento](../../docs/protocolo-alertas-sectoriales.md).

Cada tasa compara MW medios del mes completo con el mismo mes del año previo. Los umbrales son decisiones editoriales: no significancia estadística ni detección confirmada de crisis o expansión.

| Actividad | Interanual | Cambio MW | Revisión propuesta | Persistencia de 3 meses |
| --- | ---: | ---: | --- | --- |
{rows}

`prioridad`: cambio de al menos 20% y 10 MW en valor absoluto, o tres meses consecutivos cumpliendo 10% y 5 MW en la misma dirección. `observar`: al menos 10% y 5 MW, sin prioridad. `sin_umbral`: no activa esas reglas, no equivale a normalidad. La persistencia de tres meses incluye junio, julio y agosto, cada uno frente a su mismo mes de 2025.

Aluar se informa aparte: {num(al['yoy_percent'],1)}%, {num(al['delta_mw'],1)} MW, estado `{al['status']}`. Es demanda neta de red: no atribuir el cambio a producción, autogeneración ni IA sin datos adicionales. No integra el conteo de las 14 actividades.

Las categorías son usuarios GUMAs + AUTO, no un panel fijo ni toda la industria. Hay que revisar cambios de establecimientos, calendario, clima y paradas antes de interpretar cualquier señal. Septiembre de 2026 está excluido por ser parcial. Las comparaciones de agosto tienen una diferencia de {a['rows'][0]['working_day_difference']} días hábiles según la propia base; no se realizó ajuste por calendario.

La fuente sigue siendo provisoria y presenta una [discrepancia documental pendiente](discrepancias-cammesa.md). Las señales sirven para ordenar investigación, no para emitir una conclusión sectorial confirmada. El cruce con producción física debe respetar la cobertura de cada fuente.

Esta ilustración usa datos ya observados y una única captura histórica revisada. No acredita rendimiento prospectivo. [Resultados reproducibles, reglas y huella de fuente](alertas-sectoriales.json).
''')


def main():
    daily, _ = extract()
    monthly = summarize(daily)
    source = json.loads((ROOT/'data/activity_monthly_history.json').read_text())
    rules = json.loads((ROOT/'data/sector_alert_rules.json').read_text())
    d = discrepancies(daily, monthly)
    a = alert_report(monthly, source['activities'], rules)
    write_reports(d, a)
    print(json.dumps({'cross_sheet_checks': d['cross_sheet_checks'], 'calendar_checks': d['calendar_checks'],
                      'signals': [{k:r[k] for k in ['id','status','yoy_percent','delta_mw','persistent']} for r in a['rows']]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
