"""Extract archived CAMMESA XLSX cached daily observations with stdlib only.

The original workbook is never recalculated, edited or silently refreshed.
"""
import calendar
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SOURCE='data/reference/cammesa-gumas-base-2026-09-25.zip'
SHA='97c70adf2017edebd4d9e45b5981411a392e3e2f0654cf55ab7f273bd1ce8c4a'
SHEET='Base Detalle diaria GUMAs ACT'
COLS={'ports':'I','commerce':'J','food':'K','public_services':'L',
      'automotive':'N','petroleum_products':'O','construction':'P','wood_paper':'Q',
      'metals':'R','textiles':'S','chemicals':'T','steel':'U','mining':'W','oil_extraction':'X',
      'food_commerce_services':'M','industry':'V','oil_minerals':'Y','aluar':'Z','total':'H'}


def extract():
    raw=(ROOT/SOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA: raise ValueError('Source archive changed')
    with ZipFile(io.BytesIO(raw)) as outer:
        names=outer.namelist()
        if names!=['Base de datos GU Semanal.xlsx']: raise ValueError('Unexpected archive member')
        content=outer.read(names[0])
    with ZipFile(io.BytesIO(content)) as z:
        shared=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(e.itertext()) for e in shared]
        book=ET.fromstring(z.read('xl/workbook.xml'))
        sheets=book.find('s:sheets',NS)
        sid=next(s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'] for s in sheets if s.attrib['name']==SHEET)
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target=next(r.attrib['Target'] for r in rels if r.attrib['Id']==sid)
        xml=ET.fromstring(z.read(target.lstrip('/') if target.startswith('/') else 'xl/'+target))
        rows=[]
        for row in xml.findall('s:sheetData/s:row',NS):
            rn=int(row.attrib['r'])
            if rn<14: continue
            cells={''.join(filter(str.isalpha,c.attrib['r'])):c for c in row}
            def val(col):
                c=cells.get(col)
                if c is None or c.find('s:v',NS) is None: return None
                t=c.find('s:v',NS).text
                return strings[int(t)] if c.attrib.get('t')=='s' else t if c.attrib.get('t')=='str' else float(t)
            serial=val('D')
            if serial is None: continue
            month=(datetime(1899,12,30)+timedelta(days=serial)).date()
            day=date(month.year,month.month,int(val('E')))
            if month.day!=1 or val('B')!=day.year: raise ValueError('Date columns disagree')
            values={k:val(c) for k,c in COLS.items()}
            if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in values.values()): raise ValueError('Missing or invalid daily value')
            rows.append({'date':day.isoformat(),'source_row':rn,'working_day':val('F')=='Hábil','mw':values})
    validate_daily(rows)
    return rows,hashlib.sha256(content).hexdigest()


def validate_daily(rows):
    for i,row in enumerate(rows):
        d=date.fromisoformat(row['date']); v=row['mw']
        if d>date(2026,9,26): raise ValueError('Observation after capture')
        if i and d-date.fromisoformat(rows[i-1]['date'])!=timedelta(days=1): raise ValueError('Duplicate or missing daily date')
        groups=[(['ports','commerce','food','public_services'],'food_commerce_services'),
                (['automotive','petroleum_products','construction','wood_paper','metals','textiles','chemicals','steel'],'industry'),
                (['mining','oil_extraction'],'oil_minerals'),
                (['food_commerce_services','industry','oil_minerals','aluar'],'total')]
        if any(abs(sum(v[k] for k in keys)-v[total])>1e-6 for keys,total in groups): raise ValueError('Daily components do not reconcile')


def summarize(rows):
    by=defaultdict(list)
    for r in rows: by[r['date'][:7]].append(r)
    result=[]
    for period,rs in sorted(by.items()):
        year,month=map(int,period.split('-')); expected=calendar.monthrange(year,month)[1]
        complete=len(rs)==expected and rs[0]['date'].endswith('-01')
        mw={k:sum(r['mw'][k] for r in rs)/len(rs) for k in COLS}
        result.append(dict(period=period,days=len(rs),calendar_days=expected,complete_month=complete,
            start=rs[0]['date'],end=rs[-1]['date'],working_days=sum(r['working_day'] for r in rs),
            first_source_row=rs[0]['source_row'],last_source_row=rs[-1]['source_row'],mw=mw,
            aluar_net_grid_gwh=mw['aluar']*24*len(rs)/1000))
    lookup={r['period']:r for r in result}
    for r in result:
        previous=lookup.get(str(int(r['period'][:4])-1)+r['period'][4:])
        r['yoy_percent']={k:100*(r['mw'][k]/previous['mw'][k]-1) if previous and previous['complete_month'] and r['complete_month'] and previous['mw'][k]!=0 else None for k in COLS}
    return result


def build():
    daily,inner_hash=extract(); monthly=summarize(daily)
    e=json.loads((ROOT/'data/concentration_evidence.json').read_text())
    research=json.loads((ROOT/'data/aluar_monthly_research.json').read_text())
    for s in research['sources']:
        if 'local_file' in s and hashlib.sha256((ROOT/s['local_file']).read_bytes()).hexdigest()!=s['sha256']: raise ValueError('Aluar research archive changed')
    if any(v is not None for v in research['monthly_causal_attribution'].values()): raise ValueError('Monthly causal attribution unsupported')
    old=e['gumas']['periods'][0]; august=next(r for r in monthly if r['period']=='2026-08')
    result=dict(reviewed_at='2026-09-26',source=dict(publisher='CAMMESA',
        url='https://cammesaweb.cammesa.com/download/base-de-datos-2/?wpdmdl=39428',
        landing_url='https://cammesaweb.cammesa.com/2026/09/25/covid-19-comportamiento-de-la-demanda-de-energia-electrica-en-el-mem/',
        retrieved_at='2026-09-26',archive=SOURCE,sha256=SHA,member='Base de datos GU Semanal.xlsx',
        member_sha256=inner_hash,sheet=SHEET,header_row=13,columns=COLS),
        scope='GUMAs + AUTO, Aluar separado. Usuarios vigentes: no panel fijo de establecimientos. No equivale a GUMA/GUME/GUDI ni a demanda nacional.',
        method='Promedio de los MW medios diarios de todos los días disponibles. Mes completo exige todos los días consecutivos. Interanual solo entre meses completos. Energía neta de Aluar calculada = suma MW medios diarios × 24 / 1000, en GWh; no consumo bruto ni facturación DTE.',
        provisional=True,first_date=daily[0]['date'],last_date=daily[-1]['date'],daily_count=len(daily),aluar_research=research,
        activities=e['gumas']['activities'],monthly=monthly,
        revision_comparison=dict(period='2026-08',previous_document_date='2026-09-17',comparison_pdf_date='2026-09-24',comparison_pdf_total_mw=2295.2,
            previous_total_mw=old['total_mw'],current_total_mw=august['mw']['total'],delta_mw=august['mw']['total']-old['total_mw'],
            pdf_archive='data/reference/cammesa-gumas-2026-09-24.pdf',pdf_sha256='471a3c0bf65b8156d8dfd367544a25e0fa85911497031013d41733486274e189',pdf_page=7,
            note='Agosto: PDF del 17/09 = 2293,1 MW; PDF del 24/09 = 2295,2 MW; promedio de la base diaria capturada el 26/09 = 2292,0401 MW. Diferencia entre archivos/capturas, no crecimiento. No se confirmó la causa ni se sustituyen silenciosamente las ediciones anteriores.'))
    # Reuse labels only, never carry the two old snapshot values into the new series.
    result['activities']=[{k:v for k,v in a.items() if k!='values'} for a in result['activities']]
    rev=result['revision_comparison']
    if hashlib.sha256((ROOT/rev['pdf_archive']).read_bytes()).hexdigest()!=rev['pdf_sha256']: raise ValueError('Comparison PDF changed')
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    (ROOT/'data/activity_monthly_history.json').write_text(payload)
    (ROOT/'dashboard/downloads/activity_monthly_history.json').write_text(payload)
    (ROOT/'dashboard/activity-history-data.js').write_text('window.ACTIVITY_HISTORY = '+json.dumps(result,ensure_ascii=False,allow_nan=False)+';\n')
    print(f'Activity history: {len(daily)} daily records, {sum(r["complete_month"] for r in monthly)} complete months, {len(result["activities"])} activities. Last date {daily[-1]["date"]}.')
    for p in ['2025-08','2026-08']:
        r=next(r for r in monthly if r['period']==p)
        print(p,'Aluar MW',r['mw']['aluar'],'net GWh',r['aluar_net_grid_gwh'],'total',r['mw']['total'],'activities up',sum(r['yoy_percent'][a['id']]>0 for a in result['activities']))
    return result


if __name__=='__main__': build()
