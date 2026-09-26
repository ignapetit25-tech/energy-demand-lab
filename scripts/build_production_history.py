"""Extract archived INDEC XLS optionally; build same-period comparisons offline.

Extraction only: bundled Python with xlrd==2.0.2 on PYTHONPATH, --extract.
Normal build and CI use the frozen, cell-addressed extraction (stdlib only).
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

if __package__:
    from .analyze_sector_followups import pair, shift
else:
    from analyze_sector_followups import pair, shift

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'data/reference/indec-ipi-history-2026-09-26.xls'
RAW = 'data/production_history_source.json'
MONTHS = 'Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Octubre Noviembre Diciembre'.split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def col_name(i):
    text = ''
    while i >= 0:
        text = chr(65+i % 26)+text
        i = i//26-1
    return text


def extract():
    import xlrd
    book = xlrd.open_workbook(ROOT/ARCHIVE)
    mapping = json.loads((ROOT/'data/physical_production_evidence.json').read_text())['observations']
    values = {}
    for table, field in [('Cuadro 2', 'original_index'), ('Cuadro 3', 'yoy_percent')]:
        sheet = book.sheet_by_name(table)
        columns = {}
        for item in mapping:
            columns[item['electricity_activity_id']] = next(i for i, v in enumerate(sheet.row_values(2)) if str(v).removesuffix('.0') == item['code'])
        year = None
        for row in range(5, sheet.nrows):
            y, month = sheet.cell_value(row, 1), sheet.cell_value(row, 2)
            if month not in MONTHS:
                continue
            if y != '':
                year = re.search(r'\d{4}', str(y)).group()
            period = f'{year}-{MONTHS.index(month)+1:02d}'
            for key, col in columns.items():
                value = sheet.cell_value(row, col)
                if value == '///':
                    value = None
                elif not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f'Unexpected IPI value: {table} {row+1} {col+1}')
                record = values.setdefault((period, key), dict(period=period, activity_id=key))
                record[field] = value
                record[field+'_cell'] = f'{table}!{col_name(col)}{row+1}'
    result = dict(source=dict(url='https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipi_manufacturero_2026.xls',
        archive=ARCHIVE, sha256=sha(ROOT/ARCHIVE), retrieved_at='2026-09-26',
        publication_date=None, associated_report_publication='2026-09-08',
        vintage_note='Captura revisada del 26/09/2026. No se verificó fecha de publicación propia del XLS ni versiones disponibles en cada mes histórico.',
        original_index_base=2004, yoy_unit='percent', tables=['Cuadro 2', 'Cuadro 3'],
        method='IPI: volumen y otras aproximaciones. No toneladas para todas las ramas. Serie original, no desestacionalizada.',
        extraction_reader='xlrd 2.0.2'), mapping=mapping,
        observations=sorted(values.values(), key=lambda r:(r['period'],r['activity_id'])))
    (ROOT/RAW).write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return result


def build(raw, history):
    if sha(ROOT/raw['source']['archive']) != raw['source']['sha256']:
        raise ValueError('Archived IPI history changed')
    observations = raw['observations']
    indexed = {(r['period'],r['activity_id']):r for r in observations}
    if len(indexed) != len(observations):
        raise ValueError('Duplicate production observation')
    keys = {m['electricity_activity_id'] for m in raw['mapping']}
    electrical = {r['period']:r for r in history['monthly']}
    if len(electrical) != len(history['monthly']):
        raise ValueError('Duplicate electricity period')
    comparisons = []
    for r in observations:
        if r['activity_id'] not in keys or r['period'] >= raw['source']['retrieved_at'][:7]:
            raise ValueError('Unknown category or unavailable production period')
        idx, rate = r['original_index'], r['yoy_percent']
        if not isinstance(idx, (int,float)) or not math.isfinite(idx) or idx <= 0:
            raise ValueError('Invalid production index')
        old = indexed.get((shift(r['period'],-12),r['activity_id']))
        if rate is not None:
            if not isinstance(rate, (int,float)) or not math.isfinite(rate):
                raise ValueError('Invalid production rate')
            if old and abs(100*(idx/old['original_index']-1)-rate)>1e-7:
                raise ValueError('Published annual rate does not reconcile to indices')
        electricity = pair(electrical,r['period'],r['activity_id'])
        if electricity is None or rate is None:
            continue
        sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0
        comparisons.append(dict(**r,electricity_yoy_percent=electricity['yoy_percent'],
            electricity_current_mw=electricity['current_mw'],electricity_previous_mw=electricity['previous_mw'],
            electricity_delta_mw=electricity['delta_mw'],
            direction_match=sign(rate)==sign(electricity['yoy_percent']),
            direction='Ambas caen' if rate<0 and electricity['yoy_percent']<0 else 'Ambas suben' if rate>0 and electricity['yoy_percent']>0 else 'Direcciones distintas o sin cambio'))
    periods = sorted({r['period'] for r in comparisons})
    for period in periods:
        if {r['activity_id'] for r in comparisons if r['period']==period} != keys:
            raise ValueError('Unbalanced comparison month')
    summary = []
    for m in raw['mapping']:
        rows = [r for r in comparisons if r['activity_id']==m['electricity_activity_id']]
        summary.append(dict(activity_id=m['electricity_activity_id'],label=m['production_label'],
                            pairs=len(rows),matching_direction=sum(r['direction_match'] for r in rows)))
    return dict(source=raw['source'],mapping=raw['mapping'],periods=periods,comparisons=comparisons,
        summary=summary,coverage=dict(source_start=min(r['period'] for r in observations),source_end=max(r['period'] for r in observations),
        observations=len(observations),comparison_start=periods[0],comparison_end=periods[-1],comparison_count=len(comparisons)),
        interpretation='Historia descriptiva revisada. Coincidencia de signos no es validación prospectiva, causalidad, intensidad energética ni atribución de IA.',
        input_sha256={RAW:sha(ROOT/RAW),'data/activity_monthly_history.json':sha(ROOT/'data/activity_monthly_history.json')})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--extract', action='store_true'); args=parser.parse_args()
    raw = extract() if args.extract else json.loads((ROOT/RAW).read_text())
    result = build(raw, json.loads((ROOT/'data/activity_monthly_history.json').read_text()))
    (ROOT/'data/production_history.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(coverage=result['coverage'],summary=result['summary']),ensure_ascii=False))


if __name__=='__main__':
    main()
