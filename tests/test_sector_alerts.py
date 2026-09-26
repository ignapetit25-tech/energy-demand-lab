import copy
import hashlib
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from scripts.build_sector_alerts import build, physical_comparison, variant_rules
from scripts.analyze_sector_followups import classify

ROOT = Path(__file__).resolve().parents[1]


class PublishedAlertsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = json.loads((ROOT/'data/activity_monthly_history.json').read_text())
        cls.rules = json.loads((ROOT/'data/sector_alert_rules.json').read_text())
        cls.evidence = json.loads((ROOT/'data/physical_production_evidence.json').read_text())
        cls.result = build(cls.history, cls.rules, cls.evidence)

    def test_scenario_design_preserves_base_and_changes_one_factor(self):
        variants = variant_rules(self.rules)
        self.assertEqual(len(variants), 31)
        self.assertEqual(len({v['id'] for v in variants}), 31)
        self.assertEqual(next(v['rules'] for v in variants if v['id']=='w10-m5-p3'), self.rules)
        for v in variants:
            if v['family']=='one_factor':
                self.assertEqual(sum(v['rules'][k]!=self.rules[k] for k in self.rules), 1)
        self.assertFalse(self.result['deployment']['notification_enabled'])
        self.assertFalse(self.result['deployment']['automatic_refresh'])

    def test_complete_periods_and_sensitivity_bounds(self):
        d = self.result
        self.assertEqual(len(d['periods']), 44)
        self.assertEqual(d['periods'][0], '2023-01')
        self.assertEqual(d['latest_period'], '2026-08')
        self.assertNotIn('2026-09', d['periods'])
        latest = d['sensitivity']['2026-08']
        self.assertEqual((latest['min_priority'],latest['max_priority']), (4,8))
        self.assertEqual(latest['frequency']['textiles'],18)
        self.assertEqual(latest['frequency']['commerce'],10)
        for s in d['scenarios']:
            self.assertEqual(s['historical_evaluable_activity_months'], 616)
            for states in s['periods'].values():
                ids = sum([states[k] for k in ['prioridad','observar','sin_umbral','no_evaluable']], [])
                self.assertEqual(len(ids),14)
                self.assertEqual(len(set(ids)),14)
                self.assertTrue(set(states['persistent']).issubset(states['prioridad']))

    def test_base_matches_original_classifier_and_prior_report(self):
        rows = {m['period']:m for m in self.history['monthly']}
        for p in self.result['periods']:
            for r in self.result['baseline'][p]['rows']:
                self.assertEqual(r['status'], classify(rows,p,r['id'],self.rules)['status'])
        old = json.loads((ROOT/'reports/research/alertas-sectoriales.json').read_text())
        current = {r['id']:r['status'] for r in self.result['baseline']['2026-08']['rows']}
        self.assertEqual(current, {r['id']:r['status'] for r in old['rows']})

    def test_same_period_and_non_equivalent_populations(self):
        p = self.result['production']
        self.assertIsNone(p['source']['august_production_yoy_percent'])
        self.assertEqual(len(p['comparisons']),3)
        for row in p['comparisons']:
            self.assertEqual(row['production_period'], '2026-07')
            self.assertEqual(row['electricity_period'], row['production_period'])
            self.assertFalse(row['causal_inference'])
            self.assertEqual(row['direction'], 'Ambas caen')
            self.assertTrue(row['mapping'])
        construction = p['comparisons'][0]
        self.assertEqual(construction['comparison_scope'], 'proxy_parcial')
        self.assertEqual(construction['yoy_percent'], -6.9)
        self.assertAlmostEqual(construction['electricity_yoy_percent'], -15.99205495177748)

    def test_reject_unavailable_electricity_period_and_bad_dates(self):
        e = copy.deepcopy(self.evidence); e['period']='2026-09'
        with self.assertRaises(ValueError):physical_comparison(self.history,e)
        e = copy.deepcopy(self.evidence); e['published_at']='2026-10-07'
        with self.assertRaises(ValueError):physical_comparison(self.history,e)
        h = copy.deepcopy(self.history); h['monthly'].append(h['monthly'][0])
        with self.assertRaises(ValueError):build(h,self.rules,self.evidence)

    def test_saved_outputs_sources_and_javascript_payload(self):
        d = json.loads((ROOT/'dashboard/downloads/sector_alerts.json').read_text())
        for path, sha in d.pop('input_sha256').items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)
        self.assertEqual(d,self.result)
        raw = (ROOT/'dashboard/sector-alerts-data.js').read_text()
        self.assertEqual(json.loads(raw.removeprefix('window.SECTOR_ALERTS = ').removesuffix(';\n')),json.loads((ROOT/'dashboard/downloads/sector_alerts.json').read_text()))
        self.assertEqual(hashlib.sha256((ROOT/self.evidence['local_file']).read_bytes()).hexdigest(),self.evidence['sha256'])

    @unittest.skipUnless(shutil.which('pdftotext'), 'Source PDF check requires Poppler')
    def test_source_pdf_columns_not_ytd_or_incidence(self):
        for r in self.evidence['observations']:
            text = subprocess.check_output(['pdftotext','-f',str(r['page']),'-l',str(r['page']),'-layout',str(ROOT/self.evidence['local_file']),'-'],text=True)
            line = next(line for line in text.splitlines() if re.match(r'^\s*'+r['code']+r'\s+',line))
            numbers = [float(v.replace(',','.')) for v in re.findall(r'-?\d+,\d+',line)]
            self.assertEqual(numbers[0],r['original_index_base_2004'])
            self.assertEqual(numbers[1],r['yoy_percent'])


if __name__=='__main__':unittest.main()
