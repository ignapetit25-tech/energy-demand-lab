"""Reproduce reviewed numeric tables from archived originals (requires pdftotext)."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BRANCHES=[('food_commerce_services','Alimentación, comercios y servicios'),('industry','Industrias sin Aluar'),('oil_minerals','Petróleos y minerales'),('aluar','Aluar')]
LABELS={'ALIMENTACIÓN, COMERCIOS Y SERVICIOS':'food_commerce_services','INDUSTRIAS':'industry','PETROLEOS Y MINERALES':'oil_minerals','ALUAR':'aluar','INDUSTRIA ALUAR':'aluar'}
# Published subtotals/total (not sums of rounded components), in source order.
TOTALS=[(3549,3559,3990,3985),(3507,3534,3896,3886),(3620,3698,4027,4058),
        (3431,3382,3801,3749),(3466,3473,3852,3830),(3675,3952,4056,4325),
        (3628,3505,4057,3881),(3614,3487,4054,3855),(3437,3450,3976,3827),
        (3473,3449,3998,3849),(3378,3428,3924,3891),(3399,3440,3947,3816)]
MONTHS='Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Octubre Noviembre Diciembre'.split()

def text(path,page):
    return subprocess.check_output(['pdftotext','-f',str(page),'-l',str(page),'-layout',str(ROOT/path),'-']).decode()

def extract():
    sources=json.loads((ROOT/'data/reference/branch-source-manifest.json').read_text())
    observations=[];snapshots=[]
    for source,totals in zip(sources,TOTALS,strict=True):
        path=source['local_file']; raw=(ROOT/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==source['sha256']
        page=text(path,source['history_page']); month=source['period'][5:7]
        years=list(range(2018 if source['history_page']==8 else 2012,int(source['period'][:4])+1))
        columns={}
        for line in page.splitlines():
            m=re.match(r'^\s*(ALIMENTACIÓN, COMERCIOS Y SERVICIOS|PETROLEOS Y MINERALES|INDUSTRIAS|INDUSTRIA ALUAR|ALUAR)\s+((?:\d+\s+){7,}\d+)\s*$',line)
            if m:
                vals=[int(v) for v in m[2].split()]
                assert len(vals)==len(years),(path,m[1],len(vals))
                columns[LABELS[m[1]]]=vals
        assert set(columns)=={b[0] for b in BRANCHES},(path,columns.keys())
        records=[dict(period=f'{year}-{month}-01',source_period=source['period'],values={k:v[i] for k,v in columns.items()}) for i,year in enumerate(years)]
        observations.extend(records)
        comparison=text(path,source['comparison_page'])
        rates=[float(v.replace(',','.')) for v in re.findall(r'(-?\d+[.,]\d+)\s*%',comparison)]
        assert len(rates)==6,(path,rates)
        current,previous=records[-1]['values'],records[-2]['values']
        ids=['food_commerce_services','industry','oil_minerals','without_aluar','aluar','total']
        values={k:(current[k],previous[k]) for k in current}
        values.update(without_aluar=totals[:2],total=totals[2:])
        snapshots.append(dict(period=source['period'],source_period=source['period'],rows=[dict(id=k,current_mw=values[k][0],previous_mw=values[k][1],yoy_percent=rates[i]) for i,k in enumerate(ids)]))
    p='data/reference/indec-capacidad-2026-07.pdf'
    indec_keys=['food','tobacco','textiles','paper','printing','refining','chemicals','rubber_plastics','nonmetal_minerals','basic_metals','automotive','metalworking']
    indec_labels=['Alimentos y bebidas','Productos del tabaco','Productos textiles','Papel y cartón','Edición e impresión','Refinación del petróleo','Sustancias y productos químicos','Caucho y plástico','Minerales no metálicos','Industrias metálicas básicas','Industria automotriz','Metalmecánica excepto automotores']
    rows=[]
    for line in text(p,6).splitlines():
        vals=re.findall(r'\d+,\d+',line)
        if len(vals)==6 and any(line.strip().startswith(m) for m in MONTHS): rows.append([float(v.replace(',','.')) for v in vals])
    assert len(rows)==38
    general=[]
    for line in text(p,4).splitlines():
        if any(line.strip().startswith(m) for m in MONTHS):
            vals=re.findall(r'\d+,\d+',line)
            if len(vals)==1:general.append(float(vals[0].replace(',','.')))
    assert len(general)==19
    periods=[f'2025-{m:02}-01' for m in range(1,13)]+[f'2026-{m:02}-01' for m in range(1,8)]
    activity=dict(source_url='https://www.indec.gob.ar/uploads/informesdeprensa/capacidad_09_26CB3FA5C157.pdf',
                  publication_date='2026-09-15',local_file=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),pages=[4,6],
                  unit='Porcentaje de capacidad instalada utilizada',provisional=True,
                  note='Datos provisorios. Alimentos excluye actividad vitivinícola e ingenios azucareros; químicos excluye industria farmacéutica. No son categorías idénticas a las de CAMMESA. Una diferencia interanual se expresa en puntos porcentuales, no en variación de producción.',
                  sectors=[dict(id=k,label=v) for k,v in zip(indec_keys,indec_labels)],
                  observations=[dict(period=period,general_percent=general[i],values=dict(zip(indec_keys,rows[i]+rows[i+19]))) for i,period in enumerate(periods)])
    result=dict(reviewed_at='2026-09-24',branches=[dict(id=k,label=v) for k,v in BRANCHES],sources=sources,
                method='Cada mes del calendario se reconstruye de una única edición del informe: comparación entre años del mismo mes y de la misma instantánea. No se suman MW de meses distintos ni se presenta un acumulado energético. Los informes hasta julio declaran 98% de cobertura; agosto declara 90%. No se confirmó si es un cambio de muestra o de descripción. No usar la unión como serie homogénea ni atribuir variaciones a IA.',
                historical_observations=sorted(observations,key=lambda r:r['period']),monthly_snapshots=snapshots,activity=activity)
    (ROOT/'data/sector_history.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'Extracted {len(observations)} monthly branch observations, {len(snapshots)} published comparisons, {len(periods)} months × 12 INDEC sectors.')

if __name__=='__main__':extract()
