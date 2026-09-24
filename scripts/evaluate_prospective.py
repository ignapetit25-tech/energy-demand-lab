"""Score immutable forecasts against separately archived, first-recorded outcomes."""
import argparse
import csv
import hashlib
import io
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
MODELS={'primary':'primary_adaptive_annual_change_gwh','benchmark':'seasonal_naive_gwh',
        'fixed60':'fixed_60m_annual_change_gwh','drift':'seasonal_naive_expanding_drift_gwh'}


def next_month(period):
    d=date.fromisoformat(period)
    if d.day!=1:
        raise ValueError('Target must be the first day of a month')
    return date(d.year+int(d.month==12),d.month%12+1,1)


def evaluate(forecasts,outcomes,as_of):
    index={o['target_period']:o for o in outcomes}
    if len(index)!=len(outcomes):
        raise ValueError('Duplicate outcomes')
    targets={f['target_period'] for f in forecasts}
    if len(targets)!=len(forecasts) or set(index)-targets:
        raise ValueError('Duplicate forecasts or outcomes without a registered forecast')
    records=[]
    for f in forecasts:
        target=f['target_period'];issue=datetime.fromisoformat(f['issue_timestamp'])
        if issue.tzinfo is None or issue.date()>=date.fromisoformat(target):
            raise ValueError('Forecast was not issued before target month')
        record={'target_period':target,'status':'pending','actual_gwh':None,'errors':None}
        if target in index:
            o=index[target];captured=datetime.fromisoformat(o['captured_at'])
            if captured.tzinfo is None or captured.date()<next_month(target) or captured>as_of:
                raise ValueError('Outcome capture must follow completed target month and cannot be in the future')
            if not math.isfinite(o['actual_gwh']) or o['actual_gwh']<=0:
                raise ValueError('Observed demand must be positive and finite')
            if o.get('publication_date'):
                published=date.fromisoformat(o['publication_date'])
                if published<next_month(target) or published>captured.date():
                    raise ValueError('Invalid publication date')
            errors={}
            for model,key in MODELS.items():
                prediction=float(f[key])
                if not math.isfinite(prediction) or prediction<=0:
                    raise ValueError('Invalid forecast value')
                e=prediction-o['actual_gwh']
                errors[model]={'signed_gwh':e,'absolute_gwh':abs(e),'absolute_percent':abs(e)/o['actual_gwh']*100}
            record.update(status='evaluated',actual_gwh=o['actual_gwh'],errors=errors,
                          captured_at=o['captured_at'],publication_date=o.get('publication_date'),
                          source_url=o['source_url'],source_sha256=o['source_sha256'],
                          benchmark_minus_primary_absolute_gwh=errors['benchmark']['absolute_gwh']-errors['primary']['absolute_gwh'])
        records.append(record)
    done=[r for r in records if r['status']=='evaluated']
    metrics={}
    for label,group in [('overall',done),('shoulder',[r for r in done if int(r['target_period'][5:7]) in (3,4,5,9,10,11)])]:
        metrics[label]={'months':len(group),'models':{}}
        for m in MODELS:
            errors=[r['errors'][m] for r in group]
            metrics[label]['models'][m]=None if not errors else {
                'mae_gwh':sum(e['absolute_gwh'] for e in errors)/len(errors),
                'mean_error_gwh':sum(e['signed_gwh'] for e in errors)/len(errors),
                'rmse_gwh':math.sqrt(sum(e['signed_gwh']**2 for e in errors)/len(errors)),
                'mape_percent':sum(e['absolute_percent'] for e in errors)/len(errors)}
    return {'records':records,'metrics':metrics,'evaluated_months':len(done),'pending_months':len(records)-len(done),
            'interpretation':'Seguimiento descriptivo. Un mes no confirma el modelo. Consulta manual de nuevas publicaciones.'}


def build():
    with (ROOT/'prospective/forecasts.csv').open() as stream:
        forecasts=list(csv.DictReader(stream))
    outcomes=json.loads((ROOT/'prospective/outcomes.json').read_text())
    for o in outcomes:
        snapshot=(ROOT/o['snapshot_file']).resolve()
        if not snapshot.is_relative_to((ROOT/'prospective/outcome_vintages').resolve()):
            raise ValueError('Invalid outcome snapshot path')
        if hashlib.sha256(snapshot.read_bytes()).hexdigest()!=o['source_sha256']:
            raise ValueError('Outcome snapshot hash mismatch')
        observed=list(csv.DictReader(io.StringIO(snapshot.read_text())))
        matched=[r for r in observed if r['indice_tiempo']==o['target_period']]
        if len(matched)!=1 or float(matched[0]['demanda_total'])!=o['actual_gwh']:
            raise ValueError('Outcome does not match the archived source')
    result=evaluate(forecasts,outcomes,datetime.now(timezone.utc))
    (ROOT/'dashboard/prospective-data.js').write_text('window.PROSPECTIVE_DATA = '+json.dumps(result,ensure_ascii=False,allow_nan=False)+';\n')
    (ROOT/'prospective/evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(f'Prospective: {result["evaluated_months"]} evaluated, {result["pending_months"]} pending')
    return result


def record_snapshot(path,captured_at,source_url,publication_date=None):
    if urlsplit(source_url).scheme!='https' or urlsplit(source_url).hostname!='apis.datos.gob.ar':
        raise ValueError('Use the official Datos Argentina API source URL')
    captured=datetime.fromisoformat(captured_at)
    if captured.tzinfo is None or captured>datetime.now(timezone.utc):
        raise ValueError('Capture requires a timezone and cannot be in the future')
    payload=path.read_bytes();digest=hashlib.sha256(payload).hexdigest()
    rows=list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
    values={}
    for r in rows:
        period=r['indice_tiempo'];next_month(period)
        if period in values:
            raise ValueError('Duplicate source periods')
        value=float(r['demanda_total'])
        if not math.isfinite(value) or value<=0:
            raise ValueError('Invalid source demand')
        values[period]=value
    with (ROOT/'prospective/forecasts.csv').open() as stream:
        forecasts=list(csv.DictReader(stream))
    ledger=ROOT/'prospective/outcomes.json';outcomes=json.loads(ledger.read_text());index={o['target_period']:o for o in outcomes}
    snapshot_file=f'prospective/outcome_vintages/{digest}.csv'
    additions=[]
    for f in forecasts:
        period=f['target_period']
        if period not in values:
            continue
        if period in index:
            if values[period]!=index[period]['actual_gwh']:
                raise ValueError('Revision detected. Keep the first outcome; review revisions separately.')
            continue
        additions.append(dict(target_period=period,actual_gwh=values[period],captured_at=captured_at,
                              publication_date=publication_date,source_url=source_url,source_sha256=digest,snapshot_file=snapshot_file))
    evaluate(forecasts,outcomes+additions,datetime.now(timezone.utc))
    if additions:
        destination=ROOT/snapshot_file;destination.parent.mkdir(exist_ok=True)
        if destination.exists():
            if destination.read_bytes()!=payload:
                raise ValueError('Existing snapshot content differs')
        else:
            destination.write_bytes(payload)
        ledger.write_text(json.dumps(outcomes+additions,ensure_ascii=False,indent=2)+'\n')
    return build()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path);parser.add_argument('--captured-at');parser.add_argument('--source-url');parser.add_argument('--publication-date')
    args=parser.parse_args()
    if args.snapshot:
        if not args.captured_at or not args.source_url:
            parser.error('--snapshot requires --captured-at and --source-url')
        record_snapshot(args.snapshot,args.captured_at,args.source_url,args.publication_date)
    else:
        build()
