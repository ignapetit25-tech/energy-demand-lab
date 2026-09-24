"""Reproducible descriptive monthly reports. No model fitting or causal inference."""
import csv
import hashlib
import json
import math
import io
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTORS = [('residential_gwh', 'Residencial'),
           ('commerce_industry_gwh', 'Comercio e industria'),
           ('large_users_gwh', 'Grandes usuarios')]
MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
          'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def number(value, digits=1, signed=False):
    if value is None:
        return 'No disponible'
    if abs(value) < 0.5 * 10 ** -digits:
        value = 0.0
    text = f'{value:+,.{digits}f}' if signed else f'{value:,.{digits}f}'
    return text.replace(',', '_').replace('.', ',').replace('_', '.')


def month_name(period):
    return f'{MONTHS[int(period[5:7])-1]} de {period[:4]}'


def comparison(current, previous):
    return dict(current_gwh=current, previous_gwh=previous,
                delta_gwh=current-previous,
                yoy_percent=100*(current/previous-1) if previous else None)


def validate(rows):
    periods = [r['period'] for r in rows]
    if not rows or periods != sorted(set(periods)):
        raise ValueError('Periods must be unique and ordered')
    for r in rows:
        if date.fromisoformat(r['period']).day != 1:
            raise ValueError('Expected first day of month')
        for k in ['total_gwh'] + [k for k, _ in SECTORS]:
            if not math.isfinite(r[k]) or r[k] < 0:
                raise ValueError('Demand must be finite and nonnegative')
        if r['total_gwh'] <= 0 or abs(sum(r[k] for k, _ in SECTORS)-r['total_gwh']) > .01:
            raise ValueError('Sector components do not reconcile with positive total')


def make_report(rows, period):
    index = {r['period']: r for r in rows}
    current = index[period]
    year, month = int(period[:4]), int(period[5:7])
    previous_period = f'{year-1:04d}-{month:02d}-01'
    previous = index[previous_period]
    total = comparison(current['total_gwh'], previous['total_gwh'])
    sectors = []
    for key, label in SECTORS:
        item = dict(key=key, label=label, **comparison(current[key], previous[key]))
        item['share_percent'] = 100*current[key]/current['total_gwh']
        item['share_change_pp'] = item['share_percent']-100*previous[key]/previous['total_gwh']
        item['contribution_pp'] = 100*item['delta_gwh']/previous['total_gwh']
        sectors.append(item)
    periods = [f'{y:04d}-{m:02d}-01' for y in (year-1, year) for m in range(1, month+1)]
    ytd = None
    if all(p in index for p in periods):
        def aggregate(key, y):
            return sum(index[f'{y:04d}-{m:02d}-01'][key] for m in range(1, month+1))
        ytd = dict(months=month, **comparison(aggregate('total_gwh',year),aggregate('total_gwh',year-1)))
        ytd['sectors'] = [dict(key=k,label=l,**comparison(aggregate(k,year),aggregate(k,year-1))) for k,l in SECTORS]
    positive = [s for s in sectors if s['delta_gwh'] > .01]
    negative = [s for s in sectors if s['delta_gwh'] < -.01]
    headline = ('El cambio combina aumentos y caídas sectoriales.' if positive and negative else
                'El aumento se extiende a los tres sectores.' if len(positive)==3 else
                'La caída se extiende a los tres sectores.' if len(negative)==3 else
                'Los sectores muestran cambios de distinta magnitud.')
    main = max(sectors, key=lambda s: abs(s['delta_gwh']))
    summary = (f'En {month_name(period)}, la demanda fue de {number(total["current_gwh"])} GWh: '
               f'{number(total["yoy_percent"], signed=True)}% frente a {month_name(previous_period)} '
               f'({number(total["delta_gwh"], signed=True)} GWh). {headline} '
               f'{main["label"]} registró el mayor cambio absoluto: '
               f'{number(main["delta_gwh"], signed=True)} GWh y '
               f'{number(main["contribution_pp"],2,True)} puntos porcentuales del cambio total.')
    return dict(period=period, previous_period=previous_period, title=month_name(period),
                total=total, sectors=sectors, ytd=ytd, headline=headline, summary=summary)


def ai_diagnosis(r):
    c, g = r['sectors'][1:]
    return (f'En el mes seleccionado, comercio e industria varió {number(c["yoy_percent"],signed=True)}% '
            f'y grandes usuarios {number(g["yoy_percent"],signed=True)}%. '
            'Estas categorías no separan centros de datos ni cargas de IA. '
            'Ni un aumento demuestra un efecto de IA ni una caída descarta que exista carga de IA dentro del agregado.')


def monthly_csv(r, source):
    """Excel-friendly Spanish CSV: semicolon, decimal comma, UTF-8, no missing-as-zero."""
    out=io.StringIO(newline='')
    writer=csv.writer(out, delimiter=';', lineterminator='\r\n')
    writer.writerow(['mes','mes_comparacion','sector','actual_gwh','anterior_gwh','cambio_gwh',
                     'interanual_pct','aporte_pp','peso_pct','acumulado_actual_gwh',
                     'acumulado_anterior_gwh','acumulado_interanual_pct','meses_acumulados',
                     'atribucion_ia','ia_gwh','fecha_descarga','fuente_url','sha256'])
    entries=r['sectors']+[dict(label='Total',key='total',**r['total'],contribution_pp=r['total']['yoy_percent'],share_percent=100)]
    for s in entries:
        y=(r['ytd'] if s['key']=='total' else next(v for v in r['ytd']['sectors'] if v['key']==s['key'])) if r['ytd'] else {}
        values=[r['period'],r['previous_period'],s['label'],s['current_gwh'],s['previous_gwh'],s['delta_gwh'],s['yoy_percent'],s['contribution_pp'],s['share_percent'],y.get('current_gwh'),y.get('previous_gwh'),y.get('yoy_percent'),r['ytd']['months'] if r['ytd'] else None,'No identificable',None,source['downloaded_at'],source['api_query'],source['sha256']]
        writer.writerow(['' if v is None else f'{v:.6f}'.replace('.',',') if isinstance(v,float) else v for v in values])
    return out.getvalue()


def markdown(r, source, evidence=None):
    t=r['total']
    lines=[f'# Informe mensual de demanda eléctrica — {r["title"]}', '',
           f'Argentina · Diagnóstico descriptivo · Datos descargados el {source["downloaded_at"]}', '',
           r['summary'], '', '## Diagnóstico sectorial', '',
           '| Sector | GWh | Interanual | Cambio GWh | Aporte al cambio total (pp) | Peso actual |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for s in r['sectors']:
        rate = number(s['yoy_percent'],signed=True)+'%' if s['yoy_percent'] is not None else 'No disponible'
        lines.append(f'| {s["label"]} | {number(s["current_gwh"])} | {rate} | {number(s["delta_gwh"],signed=True)} | {number(s["contribution_pp"],2,True)} | {number(s["share_percent"])}% |')
    lines += ['', f'El cambio total es {number(t["yoy_percent"],2,True)}%. Los aportes sectoriales se calculan como cambio de cada sector dividido por la demanda total del mismo mes del año anterior, por 100. Suman el cambio porcentual total, salvo redondeo.', '', '## Acumulado comparable', '']
    if r['ytd']:
        y=r['ytd']
        lines += [f'Enero–{MONTHS[y["months"]-1]}: {number(y["current_gwh"])} GWh, {number(y["yoy_percent"],signed=True)}% frente a los mismos meses del año anterior.', '']
        for s in y['sectors']:
            rate = number(s['yoy_percent'],signed=True)+'%' if s['yoy_percent'] is not None else 'No disponible'
            lines.append(f'- {s["label"]}: {rate} acumulado interanual.')
    else:
        lines += ['No disponible: faltan meses para construir dos acumulados comparables.']
    if evidence:
        lines += ['', '## IA y electricidad: evidencia y límites', '', ai_diagnosis(r), '',
                  evidence['conclusion'], '',
                  f'Contexto internacional revisado el {evidence["reviewed_at"]}. Es una revisión actual: no representa información necesariamente disponible en el mes histórico seleccionado.', '']
        for e in evidence['indicators']:
            value=number(e['value'])+' '+e['unit'] if e['value'] is not None else e['unit']
            lines.append(f'- {e["geography"]} · {e["period"]} · {e["metric"]}: {value}. {e["status"]}. [{e["source_id"]}]. {e["limitation"]}')
        lines += ['', evidence['interpretation'], '', 'Siguiente investigación: '+evidence['next_data'], '', 'Fuentes de la revisión de IA:', '']
        lines += [f'- [{s["id"]}] {s["publisher"]}: {s["title"]}. {s["url"]}' for s in evidence['sources']]
    lines += ['', '## Preguntas para investigar', '',
              '- ¿Qué parte de los cambios coincide con diferencias de temperatura y calendario? Requiere controles adicionales.',
              '- ¿El patrón sectorial persiste en los próximos meses? Un solo mes no establece una tendencia.',
              '- ¿Cómo se relaciona con tarifas y actividad? Esta descomposición no identifica sus efectos.', '',
              '## Alcance y trazabilidad', '',
              'Se comparan meses iguales y acumulados de igual duración. Las series no están ajustadas por clima ni días hábiles. Las categorías se conservan tal como aparecen en la fuente: comercio e industria es una categoría conjunta y no se interpreta como industria pura; grandes usuarios no equivale exclusivamente a industria.', '',
              'Los aportes son una descomposición contable, no causas. No se estima consumo de IA o centros de datos. Este informe de observaciones no evalúa un pronóstico prospectivo. El histórico corresponde a esta descarga y puede contener revisiones; no representa la información disponible en cada fecha pasada.', '',
              f'Fuente: {source["source"]}. [Consulta de las series]({source["api_query"]}).', '',
              f'SHA-256 del archivo sectorial: `{source["sha256"]}`.', '']
    return '\n'.join(lines)


def build():
    path=ROOT/'data/raw/electricity_demand_sectors_monthly.csv'
    source=json.loads((ROOT/'data/sector_source_manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
        raise ValueError('Sector file does not match its source manifest')
    with path.open(newline='') as f:
        rows=[{k:(v if k=='period' else float(v)) for k,v in r.items()} for r in csv.DictReader(f)]
    validate(rows)
    periods={r['period'] for r in rows}
    reports=[make_report(rows,r['period']) for r in rows if f'{int(r["period"][:4])-1:04d}{r["period"][4:]}' in periods]
    evidence=json.loads((ROOT/'data/ai_energy_evidence.json').read_text())
    for report in reports:
        report['ai_diagnosis']=ai_diagnosis(report)
        report['markdown']=markdown(report,source,evidence)
        report['csv']=monthly_csv(report,source)
        # Plain text preserves source URLs and a readable aligned sector listing.
        text_lines=[]
        for line in report['markdown'].splitlines():
            if line.startswith('| ---'):
                continue
            if line.startswith('|'):
                line=' · '.join(v.strip() for v in line.strip('|').split('|'))
            text_lines.append(line.lstrip('# ').replace('`',''))
        report['text']='\n'.join(text_lines)+'\n'
    bundle=dict(source=source, evidence=evidence, reports=reports, latest_period=reports[-1]['period'])
    # The browser downloads plain text; do not ship a duplicate Markdown version per month.
    web_bundle=dict(bundle,reports=[{k:v for k,v in r.items() if k!='markdown'} for r in reports])
    (ROOT/'dashboard/report-data.js').write_text('window.MONTHLY_REPORTS = '+json.dumps(web_bundle,ensure_ascii=False,allow_nan=False,separators=(',',':'))+';\n')
    output=ROOT/'reports/monthly'
    output.mkdir(parents=True,exist_ok=True)
    latest=reports[-1]
    (output/f'{latest["period"][:7]}.md').write_text(latest['markdown'])
    (output/f'{latest["period"][:7]}.txt').write_text(latest['text'])
    (output/f'{latest["period"][:7]}.csv').write_text('\ufeff'+latest['csv'],newline='')
    (output/f'{latest["period"][:7]}.json').write_text(json.dumps(latest,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(f'Monthly reports: {len(reports)} comparable months; latest {latest["title"]}')
    return bundle


if __name__=='__main__':
    build()
