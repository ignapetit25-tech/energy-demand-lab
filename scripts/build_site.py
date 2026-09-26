"""Build a small, explicit public artifact for GitHub Pages, without dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
ASSETS = ('index.html', 'monthly-report.html', 'styles.css', 'report.css',
          'app.js', 'report.js', 'data.js', 'report-data.js', 'prospective-data.js', 'favicon.svg',
          'research-data.js','research-report.js','infrastructure.html','infrastructure.js','infrastructure.css',
          'sector-history.html','sector-history.js','sector-history.css',
          'concentration.html','concentration.css','concentration.js','concentration-data.js',
          'activity-history-data.js','activity-history.js')
DOWNLOADS = ('downloads/energy-demand.xlsx','downloads/excel-manifest.json',
             'downloads/infrastructure_registry.json','downloads/sector_deep_dive.json','downloads/sector_history.json',
             'downloads/concentration_analysis.json','downloads/activity_monthly_history.json')
DOCUMENTS = ('prospective/preregistration.md', 'results/nested_exploratory/report.md')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('src', 'href'):
            if key in attrs:
                self.refs.append(attrs[key])


def validate_site(site):
    for file in site.glob('*.html'):
        parser = Links()
        parser.feed(file.read_text(encoding='utf-8'))
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            if url.path.startswith('/'):
                raise ValueError(f'Absolute path breaks repository Pages URLs: {ref}')
            target = (file.parent / unquote(url.path)).resolve() if url.path else file
            if not target.is_relative_to(site.resolve()) or not target.is_file():
                raise ValueError(f'Missing or out-of-site link from {file.name}: {ref}')
            if not url.path and url.fragment and url.fragment not in parser.ids:
                raise ValueError(f'Missing local anchor: {ref}')


def main():
    subprocess.run([sys.executable,str(ROOT/'scripts/build_activity_history.py')],check=True,cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT/'scripts/build_dashboard.py')], check=True, cwd=ROOT)
    expected = set(ASSETS) | set(DOCUMENTS) | set(DOWNLOADS) | {'.nojekyll', 'site-manifest.json'}
    excel=json.loads((ROOT/'dashboard/downloads/excel-manifest.json').read_text())
    source=json.loads((ROOT/'data/sector_source_manifest.json').read_text())
    if excel['source_sha256']!=source['sha256'] or excel['sha256']!=hashlib.sha256((ROOT/'dashboard/downloads/energy-demand.xlsx').read_bytes()).hexdigest():
        raise ValueError('Excel is stale or modified; regenerate and verify before publishing')
    if excel.get('evidence_sha256')!=hashlib.sha256((ROOT/'data/ai_energy_evidence.json').read_bytes()).hexdigest():
        raise ValueError('Excel AI evidence is stale; regenerate before publishing')
    for p in ('data/concentration_evidence.json','data/sector_history.json','data/activity_monthly_history.json','data/aluar_monthly_research.json'):
        if excel.get('research_sha256',{}).get(p)!=hashlib.sha256((ROOT/p).read_bytes()).hexdigest():
            raise ValueError('Excel research evidence is stale: '+p)
    if SITE.exists():
        unexpected = [str(p.relative_to(SITE)) for p in SITE.rglob('*')
                      if p.is_file() and str(p.relative_to(SITE)) not in expected]
        if unexpected:
            raise ValueError(f'Unexpected files in public output; inspect before publishing: {unexpected}')
    SITE.mkdir(exist_ok=True)
    for name in ASSETS:
        content = (ROOT/'dashboard'/name).read_text(encoding='utf-8')
        if name.endswith('.html'):
            for document in DOCUMENTS:
                content = content.replace(f'href="../{document}"', f'href="{document}"')
        (SITE/name).write_text(content, encoding='utf-8')
    for document in DOCUMENTS:
        target = SITE/document
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT/document).read_bytes())
    for download in DOWNLOADS:
        target=SITE/download;target.parent.mkdir(exist_ok=True)
        target.write_bytes((ROOT/'dashboard'/download).read_bytes())
    (SITE/'.nojekyll').write_text('')
    validate_site(SITE)
    manifest = {str(p.relative_to(SITE)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(SITE.rglob('*')) if p.is_file() and p.name!='site-manifest.json'}
    (SITE/'site-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Public website ready: {SITE} ({len(manifest)} files plus manifest). Internal links verified.')


if __name__=='__main__':
    main()
