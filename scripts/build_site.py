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
          'app.js', 'report.js', 'data.js', 'report-data.js', 'favicon.svg')
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
    subprocess.run([sys.executable, str(ROOT/'scripts/build_dashboard.py')], check=True, cwd=ROOT)
    expected = set(ASSETS) | set(DOCUMENTS) | {'.nojekyll', 'site-manifest.json'}
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
    (SITE/'.nojekyll').write_text('')
    validate_site(SITE)
    manifest = {str(p.relative_to(SITE)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(SITE.rglob('*')) if p.is_file() and p.name!='site-manifest.json'}
    (SITE/'site-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Public website ready: {SITE} ({len(manifest)} files plus manifest). Internal links verified.')


if __name__=='__main__':
    main()
