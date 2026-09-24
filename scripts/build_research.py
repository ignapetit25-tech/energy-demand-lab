"""Validate curated source records and publish independent, non-causal research data."""
import hashlib
import json
import math
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]


def validate(registry, sector, verify_archive=True):
    review=date.fromisoformat(registry['reviewed_at'])
    sources={s['id']:s for s in registry['sources']}
    if len(sources)!=len(registry['sources']):
        raise ValueError('Duplicate source ID')
    for s in sources.values():
        source_date=s['date'] or s.get('retrieved_at')
        if urlsplit(s['url']).scheme!='https' or not source_date or date.fromisoformat(source_date)>review:
            raise ValueError('Invalid source URL/date')
        if verify_archive and s.get('local_file') and hashlib.sha256((ROOT/s['local_file']).read_bytes()).hexdigest()!=s['sha256']:
            raise ValueError('Technical source archive changed')
    ids=set()
    for p in registry['projects']:
        if p['id'] in ids or p['status'] not in ('anunciado','operacion_documentada'):
            raise ValueError('Duplicate project or unknown status')
        ids.add(p['id'])
        if date.fromisoformat(p['status_as_of'])>review or not p['status_source_ids']:
            raise ValueError('Missing/invalid status evidence')
        refs=p['status_source_ids']+[e['source_id'] for e in p['legal_events']]
        refs += [f['source_id'] for f in p.get('technical_facts',[])]
        refs += [p[k] for k in ('power_source_id','energy_source_id') if p[k]]
        if any(ref not in sources for ref in refs):
            raise ValueError('Unknown source ID')
        for f in p.get('technical_facts',[]):
            if not math.isfinite(f['value']) or f['value']<0 or not f['unit'] or f['kind'] not in ('anuncio','parametro_tecnico','equipamiento','ampliacion','capacidad','potencial','infraestructura'):
                raise ValueError('Invalid technical fact')
        for key in ('announced_power_mw','measured_energy_gwh','ai_share_percent'):
            value=p[key]
            if value is not None and (isinstance(value,bool) or not math.isfinite(value) or value<0):
                raise ValueError('Invalid quantity')
        if p['ai_share_percent'] is not None and p['ai_share_percent']>100:
            raise ValueError('Invalid AI share')
        if p['announced_power_mw'] is not None and not p['power_source_id']:
            raise ValueError('Power requires its own source')
        if p['measured_energy_gwh'] is not None and (not p['energy_period'] or not p['energy_source_id']):
            raise ValueError('Measured energy requires period and source, not a status or litigation')
        if any(date.fromisoformat(e['date'])>review for e in p['legal_events']):
            raise ValueError('Future legal event')
    c=sector['cammesa']
    if c['unit']!='MW' or len({r['id'] for r in c['rows']})!=len(c['rows']):
        raise ValueError('Source unit or branch identifiers changed')
    if verify_archive and hashlib.sha256((ROOT/c['local_file']).read_bytes()).hexdigest()!=c['sha256']:
        raise ValueError('CAMMESA archive does not match transcription source')
    for r in c['rows']:
        if r['kind'] not in ('component','subtotal','total') or any(not math.isfinite(r[k]) for k in ('current_mw','previous_mw','yoy_percent')):
            raise ValueError('Invalid branch observation')


def load():
    registry=json.loads((ROOT/'data/infrastructure_registry.json').read_text())
    sector=json.loads((ROOT/'data/sector_deep_dive.json').read_text())
    validate(registry,sector)
    history=json.loads((ROOT/'data/sector_history.json').read_text())
    validate_history(history)
    return dict(registry=registry,sector=sector,history=history)


def validate_history(h):
    sources={s['period']:s for s in h['sources']}
    if len(sources)!=len(h['sources']):raise ValueError('Duplicate history source')
    for s in list(sources.values())+[h['activity']]:
        if hashlib.sha256((ROOT/s['local_file']).read_bytes()).hexdigest()!=s['sha256']:
            raise ValueError('Historical source archive changed')
    ids={b['id'] for b in h['branches']}; seen=set()
    for row in h['historical_observations']:
        if row['period'] in seen or row['source_period'] not in sources or set(row['values'])!=ids:
            raise ValueError('Duplicate period or invalid branch source')
        seen.add(row['period'])
        if row['period'][5:7]!=row['source_period'][5:7] or row['period']>row['source_period']:
            raise ValueError('Calendar month/vintage mismatch')
        if any(not math.isfinite(v) or v<0 for v in row['values'].values()):raise ValueError('Invalid demand')
    snap_seen=set()
    for snap in h['monthly_snapshots']:
        if snap['period'] in snap_seen or snap['source_period']!=snap['period'] or snap['period'] not in sources:
            raise ValueError('Invalid snapshot source')
        snap_seen.add(snap['period'])
        if {r['id'] for r in snap['rows']}!=ids|{'without_aluar','total'} or len(snap['rows'])!=6:
            raise ValueError('Invalid snapshot rows')
        for r in snap['rows']:
            if any(not math.isfinite(r[k]) for k in ('current_mw','previous_mw','yoy_percent')) or r['current_mw']<0 or r['previous_mw']<=0:
                raise ValueError('Invalid published comparison')
    activity_ids={s['id'] for s in h['activity']['sectors']}; seen=set()
    for row in h['activity']['observations']:
        if row['period'] in seen or set(row['values'])!=activity_ids:raise ValueError('Invalid activity coverage')
        seen.add(row['period'])
        if any(not math.isfinite(v) or not 0<=v<=100 for v in list(row['values'].values())+[row['general_percent']]):
            raise ValueError('Invalid capacity utilization')


def build():
    bundle=load()
    (ROOT/'dashboard/research-data.js').write_text('window.RESEARCH_DATA = '+json.dumps(bundle,ensure_ascii=False,allow_nan=False)+';\n')
    for name in ('infrastructure_registry.json','sector_deep_dive.json','sector_history.json'):
        (ROOT/'dashboard/downloads'/name).write_bytes((ROOT/'data'/name).read_bytes())
    print(f'Research: {len(bundle["registry"]["projects"])} documented projects; CAMMESA branch snapshot validated')
    return bundle


if __name__=='__main__':
    build()
