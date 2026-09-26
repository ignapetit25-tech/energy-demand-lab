"""Descriptive diagnostics, not a search for a causal explanation or best metric."""
import hashlib
import json
import statistics
from pathlib import Path
from scripts.build_activity_history import extract
from scripts.analyze_sector_followups import shift

ROOT=Path(__file__).resolve().parents[1]


def build():
    history=json.loads((ROOT/'data/production_history.json').read_text())
    electricity=json.loads((ROOT/'data/activity_monthly_history.json').read_text())
    daily,_=extract()
    source_rows=[r for r in history['comparisons'] if r['activity_id']=='metals']
    rows=[]
    for r in source_rows:
        p=r['period']; groups=[[v for v in daily if v['date'].startswith(t)] for t in [p,shift(p,-12)]]
        metrics=[]
        for g in groups:
            working=[d['mw']['metals'] for d in g if d['working_day']]
            metrics.append(dict(median=statistics.median(d['mw']['metals'] for d in g),working_mean=statistics.mean(working),working_days=len(working)))
        a,b=metrics
        med=100*(a['median']/b['median']-1); work=100*(a['working_mean']/b['working_mean']-1)
        rows.append(dict(**r,median_daily_yoy_percent=med,working_day_mean_yoy_percent=work,
                         working_day_count_difference=a['working_days']-b['working_days'],
                         gap_pp=r['electricity_yoy_percent']-r['yoy_percent'],
                         material_opposite=abs(r['electricity_yoy_percent'])>0.5 and abs(r['yoy_percent'])>0.5 and not r['direction_match'],
                         median_opposite=med*r['yoy_percent']<0,working_mean_opposite=work*r['yoy_percent']<0))
    opposite=[r for r in rows if not r['direction_match']]
    sources=[dict(id='ipi_april',url='https://www.indec.gob.ar/uploads/informesdeprensa/ipi_manufacturero_06_269AB5D3D090.pdf',archive='data/reference/indec-ipi-2026-04.pdf',pages=[17],retrieved_at='2026-09-26'),
             dict(id='ipi_july_method',url='https://www.indec.gob.ar/uploads/informesdeprensa/ipi_manufacturero_09_26B810401E77.pdf',archive='data/reference/indec-ipi-2026-07.pdf',pages=[17,26],retrieved_at='2026-09-26')]
    for s in sources:s['sha256']=hashlib.sha256((ROOT/s['archive']).read_bytes()).hexdigest()
    result=dict(reviewed_at='2026-09-26',scope='43 meses enero 2023–julio 2026; productos de metal, no siderurgia ni Aluar.',
        rows=rows,divergences=opposite,summary=dict(pairs=len(rows),opposite=len(opposite),material_opposite=sum(r['material_opposite'] for r in opposite),
        opposite_after_median=sum(r['median_opposite'] for r in opposite),opposite_after_working_mean=sum(r['working_mean_opposite'] for r in opposite),
        by_year={y:sum(r['period'].startswith(y) for r in opposite) for y in ['2023','2024','2025','2026']}),
        april_case=dict(electricity_yoy_percent=next(r['electricity_yoy_percent'] for r in rows if r['period']=='2026-04'),
            first_report_ipi_yoy_percent=-1.4,revised_snapshot_ipi_yoy_percent=next(r['yoy_percent'] for r in rows if r['period']=='2026-04'),
            subgroups=[dict(label='Uso estructural',yoy_percent=3.5,contribution_pp=0.9),dict(label='Envases metálicos',yoy_percent=29.5,contribution_pp=2.0),dict(label='Otros productos y servicios de trabajo de metales',yoy_percent=-6.4,contribution_pp=-4.3)],
            interpretation='La composición del IPI es heterogénea. No se conoce el peso eléctrico de esas subclases: no se puede atribuir la divergencia a envases u otro componente.'),
        conclusion='La divergencia es recurrente y la causa no está identificada. Diferentes poblaciones y ponderaciones son limitaciones documentadas, no una explicación causal demostrada.',
        hypotheses=['Cambios de usuarios o clasificación CAMMESA: falta panel de establecimientos.', 'Composición y ponderación: IPI agrega con valor agregado base 2004, no peso eléctrico.', 'Calendario, paradas, eficiencia o autoabastecimiento: requieren mediciones adicionales.'],
        sources=sources,production_source=history['source'],electricity_source=electricity['source'],
        caveat='Mediana diaria y promedio de días hábiles son controles exploratorios, no sustituyen el promedio mensual publicado ni constituyen ajuste climático/estacional.',
        input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['data/production_history.json','data/activity_monthly_history.json']})
    return result


def report(d):
    s=d['summary'];fmt=lambda v:f'{v:+.2f}'.replace('.',',')
    lines=['# Divergencias en productos de metal','','Revisión 26/09/2026. '+d['scope'],'',d['conclusion'],'',
      f"De {s['pairs']} meses, {s['opposite']} muestran signos contrarios; {s['material_opposite']} conservan oposición con ambas tasas fuera de ±0,5%. Por año: {s['by_year']}.",'',
      '| Mes | Electricidad % | IPI % | Diferencia pp | Mediana diaria % | Media días hábiles % | Diferencia días hábiles |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in d['divergences']:lines.append('| '+r['period']+' | '+' | '.join(fmt(r[k]) for k in ['electricity_yoy_percent','yoy_percent','gap_pp','median_daily_yoy_percent','working_day_mean_yoy_percent','working_day_count_difference'])+' |')
    lines+=['',f"La oposición persiste en {s['opposite_after_median']} de esos 15 meses usando mediana diaria y en {s['opposite_after_working_mean']} usando promedio de días hábiles. No prueba ausencia de efectos de calendario o valores extremos. "+d['caveat'],'',
      '## Caso abril de 2026','',f"Electricidad: {fmt(d['april_case']['electricity_yoy_percent'])}%. El informe original de INDEC publica −1,4% en productos de metal; la captura histórica revisada da {fmt(d['april_case']['revised_snapshot_ipi_yoy_percent'])}%. La revisión no cambia el signo y se conserva, sin reemplazar una edición con otra.",'',
      'El cuadro 2.11 del informe de abril muestra uso estructural +3,5%, envases +29,5% y otros productos/servicios −6,4%. Sus incidencias son +0,9, +2,0 y −4,3 pp: suman −1,4 pp. Hay heterogeneidad dentro del agregado. No tenemos la correspondencia ni las ponderaciones eléctricas para identificar qué subclase explica la divergencia.','',
      '## Qué está documentado y qué falta','',
      'INDEC utiliza varias aproximaciones a volumen y ponderaciones de valor agregado de 2004. CAMMESA mide carga eléctrica de una selección de grandes usuarios. No se validó un panel común. No convertir su diferencia en eficiencia, elasticidad o consumo de IA.','']
    lines += ['- '+h for h in d['hypotheses']]
    lines+=['','Siguiente dato decisivo: altas/bajas y reclasificaciones mensuales de usuarios, mapeo a CLaNAE y consumo/producción con perímetro común. Las solicitudes preparadas no fueron enviadas.','','## Fuentes archivadas','']
    lines += [f"- {v['url']} · páginas {v['pages']} · SHA-256 {v['sha256']}" for v in d['sources']]
    lines += [f"- Historia INDEC: {d['production_source']['url']} · SHA-256 {d['production_source']['sha256']}",f"- Base diaria CAMMESA: {d['electricity_source']['url']} · SHA-256 {d['electricity_source']['sha256']}",'']
    return '\n'.join(lines)


if __name__=='__main__':
    d=build()
    (ROOT/'reports/research/divergencias-metales.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (ROOT/'reports/research/divergencias-metales.md').write_text(report(d))
    print(d['summary'])
