"""Append-only prospective sector registry. No scheduler, no retrospective issuance.

CLI timestamps use the actual UTC clock. IPI inputs are explicitly reviewed manual
extractions backed by archived originals, not automatically parsed measurements.
Publication proof is a public GitHub observation made now, never a git author date.
"""
import argparse
import base64
import fcntl
import hashlib
import io
import json
import math
import os
import random
import re
import subprocess
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from scripts.analyze_sector_followups import classify, shift
from scripts.build_activity_history import COLS, NS, SHEET, SOURCE, summarize

ROOT=Path(__file__).resolve().parents[1]
REPO='ignapetit25-tech/energy-demand-lab'
LEDGER='prospective/sector-alerts-ledger.json'
ARTIFACTS='prospective/sector-registry/artifacts'
PROTOCOL='prospective/sector-alerts-protocol.json'


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(raw):return hashlib.sha256(raw).hexdigest()


def timestamp(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('UTC/offset required')
    return t.astimezone(timezone.utc)


def stamp(t):return t.astimezone(timezone.utc).isoformat().replace('+00:00','Z')


def period_check(p,protocol):
    if not re.fullmatch(r'\d{4}-\d{2}',p):raise ValueError('Expected YYYY-MM')
    date.fromisoformat(p+'-01')
    if not protocol['start_period']<=p<=protocol['end_period']:raise ValueError('Outside prospective cohort')


def closed(p,now):
    if date.fromisoformat(shift(p,1)+'-01')>now.date():raise ValueError('Target month has not closed')


def sign(v):return 1 if v>0.5 else -1 if v<-.5 else 0


def verified_protocol(root=ROOT):
    p=json.loads((root/PROTOCOL).read_text())
    for file,sha in p['frozen_inputs'].items():
        if digest((root/file).read_bytes())!=sha:raise ValueError('Frozen rule/code changed')
    return p


def empty_ledger(protocol):
    return dict(schema_version=1,protocol_sha256=digest(canonical(protocol)),events=[])


def validate_chain(ledger,protocol,root=None):
    if ledger['schema_version']!=1 or ledger['protocol_sha256']!=digest(canonical(protocol)):raise ValueError('Protocol/registry mismatch')
    previous=None;last=None
    for i,e in enumerate(ledger['events']):
        raw={k:v for k,v in e.items() if k!='sha256'}
        if e['sequence']!=i+1 or e['previous_sha256']!=previous or digest(canonical(raw))!=e['sha256']:raise ValueError('Event chain modified')
        t=timestamp(e['recorded_at'])
        if last and t<last:raise ValueError('Event time regressed')
        period_check(e['period'],protocol)
        if root:
            for artifact in e['payload'].get('artifacts',[]):
                expected=f"{ARTIFACTS}/{artifact['sha256']}.bin"
                if artifact['archive']!=expected or digest((root/expected).read_bytes())!=artifact['sha256']:raise ValueError('Archived evidence changed')
        previous=e['sha256'];last=t


def append(ledger,kind,p,payload,now):
    if ledger['events'] and timestamp(ledger['events'][-1]['recorded_at'])>now:raise ValueError('Event time regressed')
    event=dict(sequence=len(ledger['events'])+1,previous_sha256=ledger['events'][-1]['sha256'] if ledger['events'] else None,
               kind=kind,period=p,recorded_at=stamp(now),payload=payload)
    event['sha256']=digest(canonical(event));ledger['events'].append(event);return event


def events(ledger,kind,p):return [e for e in ledger['events'] if e['kind']==kind and e['period']==p]


def read_zip(raw):
    with ZipFile(io.BytesIO(raw)) as outer:
        if outer.namelist()!=['Base de datos GU Semanal.xlsx']:raise ValueError('Unexpected CAMMESA archive')
        if outer.infolist()[0].file_size>100_000_000:raise ValueError('Archive too large')
        content=outer.read(outer.namelist()[0])
    with ZipFile(io.BytesIO(content)) as z:
        strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        book=ET.fromstring(z.read('xl/workbook.xml'))
        sid=next(s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'] for s in book.find('s:sheets',NS) if s.attrib['name']==SHEET)
        target=next(r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if r.attrib['Id']==sid)
        sheet=ET.fromstring(z.read(target.lstrip('/') if target.startswith('/') else 'xl/'+target))
        def value(c):
            v=c.find('s:v',NS)
            if v is None:return None
            return strings[int(v.text)] if c.attrib.get('t')=='s' else v.text if c.attrib.get('t')=='str' else float(v.text)
        rows=[];header=None
        for row in sheet.findall('s:sheetData/s:row',NS):
            rn=int(row.attrib['r']);v={re.sub('[0-9]','',c.attrib['r']):value(c) for c in row}
            if rn==13:header=v
            if rn<14 or v.get('D') is None:continue
            month=(datetime(1899,12,30)+timedelta(days=v['D'])).date()
            day=date(month.year,month.month,int(v['E']))
            if month.day!=1 or v['B']!=day.year or v['E']!=day.day or v['F'] not in ['Hábil','No Hábil']:raise ValueError('Unexpected date/calendar layout')
            rows.append(dict(date=day.isoformat(),source_row=rn,working_day=v['F']=='Hábil',mw={k:v.get(c) for k,c in COLS.items()}))
    return rows,header


def monthly_source(raw,captured_at,now,p,protocol):
    period_check(p,protocol);closed(p,now)
    captured=timestamp(captured_at)
    if captured>now or captured.date()<date.fromisoformat(shift(p,1)+'-01'):raise ValueError('Invalid electricity capture time')
    rows,header=read_zip(raw)
    _,expected_header=read_zip((ROOT/SOURCE).read_bytes())
    if header!=expected_header:raise ValueError('CAMMESA layout changed; review before ingestion')
    if not rows:raise ValueError('Empty electricity archive')
    for i,r in enumerate(rows):
        day=date.fromisoformat(r['date']);v=r['mw']
        if day>captured.date() or (i and day-date.fromisoformat(rows[i-1]['date'])!=timedelta(days=1)):raise ValueError('Missing, duplicate or future day')
        if any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in v.values()):raise ValueError('Invalid daily power')
        groups=[(['ports','commerce','food','public_services'],'food_commerce_services'),(['automotive','petroleum_products','construction','wood_paper','metals','textiles','chemicals','steel'],'industry'),(['mining','oil_extraction'],'oil_minerals'),(['food_commerce_services','industry','oil_minerals','aluar'],'total')]
        if any(abs(sum(v[k] for k in ks)-v[total])>1e-6 for ks,total in groups):raise ValueError('Power components do not reconcile')
    monthly={r['period']:r for r in summarize(rows)}
    for delta in [0,-1,-2,-12,-13,-14]:
        m=monthly.get(shift(p,delta))
        if not m or not m['complete_month']:raise ValueError('Missing complete comparator/persistence month')
    return monthly


def reviewed_ipi(record,now,protocol,target=None):
    """Validate reviewed transcription. Does not pretend to parse/verify PDF cells."""
    if record.get('reviewed') is not True or not str(record.get('reviewer','')).strip():raise ValueError('Explicit human extraction review required')
    p=record['period'];date.fromisoformat(p+'-01')
    if target is not None and p!=target:raise ValueError('IPI target month mismatch')
    pub=record['published_at']; published=timestamp(pub+'T00:00:00Z' if len(pub)==10 else pub)
    captured=timestamp(record['captured_at'])
    if published>captured or captured>now or p>=published.strftime('%Y-%m'):raise ValueError('Invalid IPI availability dates')
    if urlsplit(record['source_url']).scheme!='https' or urlsplit(record['source_url']).hostname not in ['www.indec.gob.ar','biblioteca.indec.gob.ar']:raise ValueError('Expected official INDEC source')
    if set(record['observations'])!=set(protocol['activity_ids']):raise ValueError('Require all three mapped categories')
    for key,row in record['observations'].items():
        v=row['yoy_percent']
        if row['code']!=protocol['indec_codes'][key] or not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v< -100:raise ValueError('Invalid IPI code/rate')
        if not row.get('locator'):raise ValueError('IPI page/table/cell locator required')
    return record


def issue(ledger,p,monthly,baseline,source,protocol,rules,now):
    period_check(p,protocol);closed(p,now)
    if baseline:
        reviewed_ipi(baseline,now,protocol)
        if baseline['period']>=p or baseline.get('latest_known_attestation') is not True:raise ValueError('Baseline must be last known earlier IPI, reviewed at issuance')
    if timestamp(source['captured_at'])>now or timestamp(source['captured_at']).date()<date.fromisoformat(shift(p,1)+'-01'):raise ValueError('Electricity capture before close or in future')
    if events(ledger,'issue',p):raise ValueError('Signal already issued; never overwrite or reissue')
    activities=json.loads((ROOT/'data/activity_monthly_history.json').read_text())['activities']
    rows=[dict(id=a['id'],label=a['label'],**classify(monthly,p,a['id'],rules)) for a in activities]
    if any(r['status']=='no_evaluable' or not r.get('persistence_evaluable') for r in rows):raise ValueError('Signal requires complete usable history')
    return append(ledger,'issue',p,dict(rows=rows,aluar=classify(monthly,p,'aluar',rules),baseline=baseline,source=source,
        rule_version=protocol['rule_version'],protocol_sha256=digest(canonical(protocol)),
        artifacts=[],publication_status='pending_public_verification'),now)


def publication(ledger,p,commit,public_ledger,proof,protocol,now):
    period_check(p,protocol)
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Full commit SHA required')
    signal=events(ledger,'issue',p)
    if not signal:raise ValueError('No issued signal')
    validate_chain(public_ledger,protocol)
    if signal[0] not in public_ledger['events']:raise ValueError('Public commit does not contain identical issued signal')
    if events(ledger,'publication',p):raise ValueError('Public observation already recorded')
    return append(ledger,'publication',p,dict(issue_sha256=signal[0]['sha256'],commit=commit,
        verified_public_at=stamp(now),url=f'https://github.com/{REPO}/blob/{commit}/{LEDGER}',artifacts=[proof]),now)


def outcome(ledger,p,record,protocol,now):
    period_check(p,protocol);closed(p,now);reviewed_ipi(record,now,protocol,p)
    signal=events(ledger,'issue',p)
    if not signal:raise ValueError('No issued signal; use exclusion for missed month')
    if timestamp(record['captured_at'])<=timestamp(signal[0]['recorded_at']):raise ValueError('Outcome capture must follow issuance')
    old=events(ledger,'outcome',p)+events(ledger,'revision',p)
    if any(e['payload']['record']==record for e in old):return None
    if old and timestamp(record['captured_at'])<=max(timestamp(e['payload']['record']['captured_at']) for e in old):raise ValueError('Revision capture must follow prior registered outcomes')
    kind='revision' if old else 'outcome'
    return append(ledger,kind,p,dict(record=record,artifacts=[]),now)


def assess(ledger,protocol,now):
    validate_chain(ledger,protocol)
    periods=[shift(protocol['start_period'],i) for i in range(protocol['months'])]
    rows=[];by_month=[]
    for p in periods:
        sig=events(ledger,'issue',p);pub=events(ledger,'publication',p);out=events(ledger,'outcome',p);exc=events(ledger,'exclusion',p)
        status='pendiente_de_emision' if not sig else 'pendiente_de_resultado' if not out else 'registrado'
        if exc and not out:status='excluido_documentado'
        by_month.append(dict(period=p,status=status,issued=bool(sig),outcome=bool(out),exclusion=exc[-1]['payload']['reason'] if exc else None,revisions=len(events(ledger,'revision',p))))
        if not sig or not out:continue
        baseline=sig[0]['payload']['baseline'];record=out[0]['payload']['record']
        raw_pub=record['published_at']; cutoff=timestamp(raw_pub+'T00:00:00Z' if len(raw_pub)==10 else raw_pub)
        reason=None
        if not pub:reason='emision_no_verificable'
        elif timestamp(pub[0]['payload']['verified_public_at'])>=cutoff:reason='emision_tardia'
        elif baseline is None:reason='sin_comparador_archivado'
        for key in protocol['activity_ids']:
            s=next(r for r in sig[0]['payload']['rows'] if r['id']==key)
            target=sign(record['observations'][key]['yoy_percent'])
            eligible=reason is None
            rows.append(dict(period=p,activity_id=key,priority=s['status']=='prioridad',eligible=eligible,exclusion_reason=reason,
                signal_correct=int(sign(s['yoy_percent'])==target) if eligible else None,
                baseline_correct=int(sign(baseline['observations'][key]['yoy_percent'])==target) if eligible else None))
    def metrics(rs):
        if not rs:return None
        a=sum(r['signal_correct'] for r in rs);b=sum(r['baseline_correct'] for r in rs)
        return dict(n=len(rs),signal_correct=a,baseline_correct=b,signal_accuracy=a/len(rs),baseline_accuracy=b/len(rs),difference_pp=100*(a-b)/len(rs))
    eligible=[r for r in rows if r['eligible']];primary=[r for r in eligible if r['priority']]
    resolved=all(v['outcome'] or v['status']=='excluido_documentado' for v in by_month)
    final=now.date()>=date.fromisoformat(shift(protocol['end_period'],1)+'-01') and resolved
    interval=None;decision='pendiente';empty_fraction=None
    if final:
        if len(primary)<protocol['minimum_priority_pairs'] or len({r['period'] for r in primary})<protocol['minimum_distinct_months']:decision='insuficiente'
        else:
            rng=random.Random(protocol['bootstrap']['seed']);diffs=[];empty=0
            grouped={p:[r for r in primary if r['period']==p] for p in periods}
            for _ in range(protocol['bootstrap']['replicates']):
                sample=[r for p in rng.choices(periods,k=len(periods)) for r in grouped[p]]
                if not sample:empty+=1
                else:diffs.append(metrics(sample)['difference_pp'])
            empty_fraction=empty/protocol['bootstrap']['replicates'];diffs.sort()
            def quantile(q):
                x=(len(diffs)-1)*q;lo=math.floor(x);hi=math.ceil(x);return diffs[lo]+(diffs[hi]-diffs[lo])*(x-lo)
            if diffs:interval=[quantile(.025),quantile(.975)]
            decision='favorable_limitada' if interval and interval[0]>0 and metrics(primary)['difference_pp']>=protocol['minimum_accuracy_improvement_pp'] and empty_fraction<=protocol['bootstrap']['maximum_empty_fraction'] else 'no_favorable'
    return dict(protocol_version=protocol['version'],window=[protocol['start_period'],protocol['end_period']],
        months=by_month,rows=rows,primary_metrics=metrics(primary),secondary_metrics=metrics(eligible),
        category_metrics={k:metrics([r for r in primary if r['activity_id']==k]) for k in protocol['activity_ids']},
        eligible_pairs=len(eligible),possible_pairs=36,priority_pairs=len(primary),interval_95_pp=interval,
        bootstrap_empty_fraction=empty_fraction,closed=final,decision=decision,
        issued_months=sum(m['issued'] for m in by_month),outcome_months=sum(m['outcome'] for m in by_month),
        automatic_refresh=False,notifications=False)


def archive(raw):
    sha=digest(raw);path=ROOT/ARTIFACTS/(sha+'.bin');path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Hash collision/archive changed')
    else:path.write_bytes(raw)
    return dict(archive=str(path.relative_to(ROOT)),sha256=sha)


def load_ipi(path,now,protocol):
    raw=Path(path).read_bytes();record=json.loads(raw);reviewed_ipi(record,now,protocol)
    original=Path(record.pop('archive')).read_bytes()
    if digest(original)!=record['sha256']:raise ValueError('IPI original hash mismatch')
    evidence=archive(original);record['archive']=evidence['archive']
    return record,[evidence,archive(raw)]


def save(ledger,previous):
    path=ROOT/LEDGER
    if path.read_bytes()!=previous:raise ValueError('Registry changed concurrently; retry without overwriting')
    fd,name=tempfile.mkstemp(prefix='sector-ledger-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(json.dumps(ledger,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    q=sub.add_parser('issue');q.add_argument('--period',required=True);q.add_argument('--electricity',required=True);q.add_argument('--captured-at',required=True);q.add_argument('--source-url',required=True);q.add_argument('--baseline')
    q=sub.add_parser('attest-publication');q.add_argument('--period',required=True);q.add_argument('--commit',required=True)
    q=sub.add_parser('outcome');q.add_argument('--period',required=True);q.add_argument('--record',required=True)
    q=sub.add_parser('exclude');q.add_argument('--period',required=True);q.add_argument('--reason',required=True)
    sub.add_parser('status');args=parser.parse_args();now=datetime.now(timezone.utc)
    protocol=verified_protocol();previous=(ROOT/LEDGER).read_bytes();ledger=json.loads(previous);validate_chain(ledger,protocol,ROOT)
    if args.command=='status':print(json.dumps(assess(ledger,protocol,now),ensure_ascii=False,indent=2));return
    period_check(args.period,protocol)
    if args.command=='issue':
        raw=Path(args.electricity).read_bytes();monthly=monthly_source(raw,args.captured_at,now,args.period,protocol)
        if urlsplit(args.source_url).scheme!='https' or urlsplit(args.source_url).hostname!='cammesaweb.cammesa.com':raise ValueError('Expected official CAMMESA URL')
        baseline,artifacts=load_ipi(args.baseline,now,protocol) if args.baseline else (None,[])
        electric=archive(raw)
        event=issue(ledger,args.period,monthly,baseline,dict(**electric,url=args.source_url,captured_at=args.captured_at),protocol,json.loads((ROOT/'data/sector_alert_rules.json').read_text()),now)
        code=archive(Path(__file__).read_bytes());normalized=archive(canonical(monthly))
        event['payload']['implementation']=code
        event['payload']['normalized_electricity']=normalized
        event['payload']['artifacts']=artifacts+[electric,code,normalized]
    elif args.command=='attest-publication':
        if not re.fullmatch('[0-9a-f]{40}',args.commit):raise ValueError('Full commit SHA required')
        def api(route):return json.loads(subprocess.check_output(['gh','api',route],text=True))
        repo=api('repos/'+REPO)
        if repo['private']:raise ValueError('Repository is not public')
        response=api(f'repos/{REPO}/contents/{LEDGER}?ref={args.commit}')
        public=json.loads(base64.b64decode(response['content']))
        signal=events(ledger,'issue',args.period)
        if not signal or signal[0] not in public['events']:raise ValueError('Public commit lacks identical issue')
        checked=[]
        for artifact in signal[0]['payload']['artifacts']:
            raw=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',f'repos/{REPO}/contents/{artifact["archive"]}?ref={args.commit}'])
            if digest(raw)!=artifact['sha256']:raise ValueError('Public evidence missing or hash mismatch')
            checked.append(artifact)
        proof=archive(canonical(dict(repository=repo['full_name'],visibility=repo['visibility'],response=response,verified_artifacts=checked)))
        # Conservative actual observation time, never the user-controlled commit date.
        now=datetime.now(timezone.utc);event=publication(ledger,args.period,args.commit,public,proof,protocol,now)
    elif args.command=='outcome':
        record,artifacts=load_ipi(args.record,now,protocol);event=outcome(ledger,args.period,record,protocol,now)
        if event is None:print('Identical observation already registered; no write.');return
        event['payload']['artifacts']=artifacts
    else:
        closed(args.period,now)
        if not args.reason.strip():raise ValueError('Exclusion requires reason')
        event=append(ledger,'exclusion',args.period,dict(reason=args.reason.strip(),artifacts=[]),now)
    event['sha256']=digest(canonical({k:v for k,v in event.items() if k!='sha256'}))
    validate_chain(ledger,protocol,ROOT);save(ledger,previous)
    print(json.dumps(dict(event=event['kind'],period=event['period'],sha256=event['sha256']),ensure_ascii=False))


if __name__=='__main__':
    (ROOT/'work').mkdir(exist_ok=True)
    with (ROOT/'work/sector-registry.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        main()
