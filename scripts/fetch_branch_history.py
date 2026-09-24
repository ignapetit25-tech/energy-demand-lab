"""Fetch public CAMMESA originals; never silently replace an archived source."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERIODS = [f'2025-{m:02}' for m in range(9, 13)] + [f'2026-{m:02}' for m in range(1, 8)]

def fetch(period):
    page=f'https://cammesaweb.cammesa.com/download/evolucion-de-la-demanda-por-rama-y-actividad-{period}/'
    html=subprocess.check_output(['curl','-fsSL','--retry','1','--connect-timeout','8','--max-time','30',page]).decode()
    urls=re.findall(r'(?:href|data-downloadurl)="([^"]+wpdmdl=[^"]+)"',html)
    urls=[u.replace('&amp;','&') for u in urls if '/download/evolucion-de-la-demanda' in u]
    if len(set(urls))!=1: raise ValueError(f'{period}: missing/ambiguous original: {urls}')
    url=urls[0].split('&refresh=')[0]
    raw=subprocess.check_output(['curl','-fsSL','--retry','1','--connect-timeout','8','--max-time','45',url])
    if not raw.startswith(b'%PDF'): raise ValueError(f'{period}: not a PDF')
    local=f'data/reference/cammesa-ramas-{period}.pdf'
    path=ROOT/local
    if path.exists() and path.read_bytes()!=raw: raise ValueError(f'{period}: source revision; review before replacement')
    if not path.exists(): path.write_bytes(raw)
    creation=re.search(r'Fecha de creaci[oó]n.*?(\d{2}/\d{2}/\d{4})',html,re.S)
    record=dict(period=period+'-01',source_url=page,download_url=url,local_file=local,
                sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
                captured_at=datetime.now(timezone.utc).isoformat(),
                publication_date=datetime.strptime(creation[1],'%d/%m/%Y').date().isoformat() if creation else None)
    print(json.dumps(record),flush=True)
    return record

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(fetch,PERIODS))
    # A fetch log, not the curated dataset. Review the original tables before using.
    (ROOT/'work/branch-fetch-log.json').write_text(json.dumps(records,indent=2)+'\n')
