"""Accounting decompositions, never causal attribution or merged statistical populations."""
import hashlib
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH_IDS = ('food_commerce_services', 'industry', 'oil_minerals', 'aluar')


def percent_change(current, previous):
    return 100 * (current / previous - 1) if previous else None


def net_share(delta, total_delta):
    # A positive-growth contribution share is undefined if total growth is not positive.
    return 100 * delta / total_delta if total_delta > 1e-9 else None


def validate_evidence(e, archives=True):
    review = date.fromisoformat(e['reviewed_at'])
    sources = {s['id']: s for s in e['sources']}
    if len(sources) != len(e['sources']):
        raise ValueError('Duplicate source')
    for s in sources.values():
        if not s['url'].startswith('https://') or date.fromisoformat(s['document_date']) > review:
            raise ValueError('Invalid source URL/date')
        if date.fromisoformat(s['retrieved_at']) > review or not s['pages']:
            raise ValueError('Invalid capture/page provenance')
        if archives and hashlib.sha256((ROOT/s['local_file']).read_bytes()).hexdigest() != s['sha256']:
            raise ValueError('Archive changed')
    previous_end = None
    for r in e['aluar']['observations']:
        start, end = date.fromisoformat(r['start']), date.fromisoformat(r['end'])
        if start >= end or end > review or (previous_end and start <= previous_end) or r['source_id'] not in sources:
            raise ValueError('Invalid annual period or source')
        previous_end = end
        values = [v for v in r.values() if isinstance(v, (float, int))]
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError('Invalid annual quantity')
        if r['electricity_mwh'] != r['electrolysis_mwh'] + r['other_plant_mwh']:
            raise ValueError('Plant uses do not reconcile')
        supplied = sum(r[k] for k in ('grid_contract_mwh', 'thermal_self_supply_mwh', 'wind_self_supply_mwh'))
        if r['electricity_mwh'] - supplied != r['unreconciled_mwh']:
            raise ValueError('Unacknowledged source discrepancy')
    if len(e['aluar']['observations']) != 2:
        raise ValueError('Expected two annual observations')
    if any(v is not None for k,v in e['aluar']['monthly_attribution'].items() if k.endswith('_percent')):
        raise ValueError('Annual reports do not identify monthly causal shares')
    g = e['gumas']; periods = {p['id']: p for p in g['periods']}
    if g['source_id'] not in sources or g['unit'] != 'MW medios' or len(periods) != len(g['periods']):
        raise ValueError('Invalid GUMA scope')
    if len(g['activities']) != 14 or len({a['id'] for a in g['activities']}) != 14:
        raise ValueError('Invalid activity identifiers')
    for a in g['activities']:
        if a['branch'] not in BRANCH_IDS[:3] or set(a['values']) != set(periods):
            raise ValueError('Invalid activity coverage')
        if any(not math.isfinite(v) or v < 0 for v in a['values'].values()):
            raise ValueError('Invalid activity value')
    for p in periods.values():
        start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
        if (end-start).days+1 != p['days'] or end > review:
            raise ValueError('Wrong observation window')
        next_day = date.fromordinal(end.toordinal()+1)
        complete = start.day == 1 and next_day.day == 1 and start.month == end.month
        if p['complete_month'] != complete:
            raise ValueError('Partial month mislabeled')
        if set(p['branches']) != set(BRANCH_IDS[:3]):
            raise ValueError('Missing or duplicate branch scope')
        for branch, total in p['branches'].items():
            subtotal = sum(a['values'][p['id']] for a in g['activities'] if a['branch'] == branch)
            if abs(subtotal-total) > .21:
                raise ValueError('Activity subtotal does not reconcile within rounding')
        if abs(sum(p['branches'].values()) - p['without_aluar_mw']) > .21 or abs(p['without_aluar_mw'] + p['aluar_mw'] - p['total_mw']) > .21:
            raise ValueError('GUMA total does not reconcile')
    m = g['matched_september']
    for prefix in ('current','previous'):
        if (date.fromisoformat(m[prefix+'_end'])-date.fromisoformat(m[prefix+'_start'])).days+1 != m['days_each']:
            raise ValueError('Unmatched comparison window')
    if m['current_start'][5:] != m['previous_start'][5:] or m['current_end'][5:] != m['previous_end'][5:]:
        raise ValueError('Different calendar windows')
    if int(m['current_start'][:4])-int(m['previous_start'][:4]) != 1 or date.fromisoformat(m['current_end']) > review:
        raise ValueError('Invalid interannual comparison date')
    if len(m['rows']) != 4 or {r['id'] for r in m['rows']} != set(BRANCH_IDS):
        raise ValueError('Invalid matched branch coverage')
    if any(not math.isfinite(r[k]) for r in m['rows'] for k in ('current_mw','previous_mw','published_delta_mw','published_yoy_percent')):
        raise ValueError('Nonfinite matched comparison')


def derive(reports, source, history, evidence):
    validate_evidence(evidence)
    latest = reports[-1]
    national = dict(period=latest['period'], source=source, comparisons={})
    for name, container, sectors in [('month',latest['total'],latest['sectors']), ('ytd',latest['ytd'],latest['ytd']['sectors'])]:
        national['comparisons'][name] = dict(total=container, rows=[dict(
            label=r['label'], current_gwh=r['current_gwh'], previous_gwh=r['previous_gwh'],
            delta_gwh=r['delta_gwh'], contribution_pp=100*r['delta_gwh']/container['previous_gwh'],
            net_growth_share_percent=net_share(r['delta_gwh'],container['delta_gwh'])) for r in sectors])
    branches=[]
    for snap in history['monthly_snapshots']:
        rows={r['id']:r for r in snap['rows']}; total=rows['total']; delta=total['current_mw']-total['previous_mw']
        changes=[]
        for key in BRANCH_IDS:
            r=rows[key]; d=r['current_mw']-r['previous_mw']
            changes.append(dict(**r,delta_mw=d,contribution_pp=100*d/total['previous_mw'],net_growth_share_percent=net_share(d,delta),current_share_percent=100*r['current_mw']/total['current_mw']))
        branches.append(dict(period=snap['period'],total=total,total_delta_mw=delta,rows=changes,
            positive_branches=sum(r['yoy_percent']>0 for r in changes),without_aluar_yoy_percent=rows['without_aluar']['yoy_percent'],
            rounding_residual_mw=delta-sum(r['delta_mw'] for r in changes)))
    metrics=[('production_tonnes','Producción de aluminio líquido','t'),('electricity_mwh','Consumo total de la planta','MWh'),('grid_contract_mwh','Sistema nacional / contrato Futaleufú','MWh'),('thermal_self_supply_mwh','Abastecimiento térmico propio','MWh'),('wind_self_supply_mwh','Abastecimiento eólico propio','MWh')]
    previous,current=evidence['aluar']['observations']
    annual=[dict(id=k,label=label,unit=unit,previous=previous[k],current=current[k],delta=current[k]-previous[k],change_percent=percent_change(current[k],previous[k])) for k,label,unit in metrics]
    a=history['activity']; by={r['period']:r for r in a['observations']}; persistence=[]
    for s in a['sectors']:
        pairs=[(r,by[str(int(r['period'][:4])-1)+r['period'][4:]]) for r in a['observations'] if str(int(r['period'][:4])-1)+r['period'][4:] in by]
        diffs=[r['values'][s['id']]-p['values'][s['id']] for r,p in pairs]
        persistence.append(dict(**s,comparisons=len(diffs),up=sum(v>0 for v in diffs),down=sum(v<0 for v in diffs),flat=sum(v==0 for v in diffs)))
    return dict(reviewed_at=evidence['reviewed_at'],evidence=evidence,national=national,branch_comparisons=branches,
        branch_labels=history['branches'],branch_sources=history['sources'],aluar_annual_comparison=annual,
        indec_persistence=persistence,indec_source={k:v for k,v in a.items() if k!='observations'},
        methods=dict(national='Cambio sectorial / cambio total positivo: participación en aumento neto, no en consumo. Puede superar 100% o ser negativa; queda nula si el cambio total no es positivo.',
        branches='Niveles MW redondeados: los aportes calculados no reemplazan las tasas publicadas. Se conserva cualquier residuo de redondeo. No se suman meses ni universos distintos.',
        causality='Descomposición contable. No estima efectos de producción, autogeneración, clima, tarifas o IA.'))


def build(reports, source, history):
    evidence=json.loads((ROOT/'data/concentration_evidence.json').read_text())
    result=derive(reports,source,history,evidence)
    result['input_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        'data/concentration_evidence.json','data/sector_history.json','data/raw/electricity_demand_sectors_monthly.csv')}
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    (ROOT/'dashboard/downloads/concentration_analysis.json').write_text(payload)
    (ROOT/'dashboard/concentration-data.js').write_text('window.CONCENTRATION_DATA = '+json.dumps(result,ensure_ascii=False,allow_nan=False)+';\n')
    return result
