import csv
import io
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class AIReportTests(unittest.TestCase):
    def test_source_scope_and_missingness(self):
        e=json.loads((ROOT/'data/ai_energy_evidence.json').read_text())
        sources={s['id'] for s in e['sources']}
        for row in e['indicators']:
            self.assertIn(row['source_id'],sources)
            self.assertTrue(row['limitation'])
        byid={r['id']:r for r in e['indicators']}
        self.assertEqual(byid['ai_dc_growth']['value'],50)
        self.assertIn('Proyección',byid['dc_projection']['status'])
        self.assertIsNone(byid['argentina_loi']['value'])

    def test_all_month_csvs_reconcile_and_keep_unknown_ai_blank(self):
        bundle=json.loads((ROOT/'dashboard/report-data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
        for report in bundle['reports']:
            rows=list(csv.DictReader(io.StringIO(report['csv']),delimiter=';'))
            self.assertEqual(len(rows),4)
            self.assertEqual(rows[-1]['sector'],'Total')
            for row in rows:
                self.assertEqual(row['mes'],report['period'])
                self.assertEqual(row['ia_gwh'],'')
                self.assertEqual(row['atribucion_ia'],'No identificable')
                self.assertEqual(row['sha256'],bundle['source']['sha256'])
            n=lambda row,k:float(row[k].replace(',','.'))
            self.assertAlmostEqual(sum(n(row,'actual_gwh') for row in rows[:3]),n(rows[-1],'actual_gwh'),places=4)
            self.assertAlmostEqual(sum(n(row,'aporte_pp') for row in rows[:3]),n(rows[-1],'interanual_pct'),places=4)
            self.assertIn('no representa información necesariamente disponible',report['text'])
            self.assertIn('https://www.iea.org/',report['text'])
