import tempfile
import unittest
from pathlib import Path

from scripts.build_site import validate_site


class SiteLinkTests(unittest.TestCase):
    def test_relative_assets_and_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'app.js').write_text('')
            (root/'index.html').write_text('<main id="report"></main><a href="#report">Report</a><script src="app.js"></script>')
            validate_site(root)

    def test_rejects_broken_absolute_and_outside_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for ref in ('missing.html','/styles.css','../private.txt','#absent'):
                with self.subTest(ref=ref):
                    (root/'index.html').write_text(f'<a href="{ref}">Link</a>')
                    with self.assertRaises(ValueError):
                        validate_site(root)
