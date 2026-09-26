import json
import shutil
import unittest
from pathlib import Path

from scripts.analyze_sector_followups import classify, discrepancies, alert_report, shift
from scripts.build_activity_history import extract, summarize

ROOT = Path(__file__).resolve().parents[1]


class SectorFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads((ROOT/'data/sector_alert_rules.json').read_text())
        cls.daily, _ = extract()
        cls.monthly = summarize(cls.daily)
        cls.labels = json.loads((ROOT/'data/activity_monthly_history.json').read_text())['activities']

    def sample(self, current=110, previous=100):
        return {p: dict(period=p, complete_month=True, working_days=20, mw={'x': v})
                for p, v in [('2026-08', current), ('2025-08', previous)]}

    def test_inclusive_thresholds_and_two_requirements(self):
        self.assertEqual(classify(self.sample(110), '2026-08', 'x', self.rules)['status'], 'observar')
        self.assertEqual(classify(self.sample(120), '2026-08', 'x', self.rules)['status'], 'prioridad')
        self.assertEqual(classify(self.sample(80), '2026-08', 'x', self.rules)['status'], 'prioridad')
        self.assertEqual(classify(self.sample(109.999), '2026-08', 'x', self.rules)['status'], 'sin_umbral')
        self.assertEqual(classify(self.sample(12, 10), '2026-08', 'x', self.rules)['status'], 'sin_umbral')

    def test_missing_partial_zero_and_invalid(self):
        for field, value in [('complete_month', False), ('mw', {'x': None}), ('mw', {'x': float('nan')}), ('mw', {'x': -1})]:
            rows = self.sample(); rows['2026-08'][field] = value
            self.assertEqual(classify(rows, '2026-08', 'x', self.rules)['status'], 'no_evaluable')
        self.assertEqual(classify(self.sample(10, 0), '2026-08', 'x', self.rules)['status'], 'no_evaluable')
        self.assertEqual(classify(self.sample(0, 100), '2026-08', 'x', self.rules)['yoy_percent'], -100)
        rows = self.sample(); del rows['2025-08']
        self.assertEqual(classify(rows, '2026-08', 'x', self.rules)['status'], 'no_evaluable')

    def test_persistence_requires_contiguous_same_direction(self):
        rows = self.sample()
        for month in ['06', '07']:
            for year, v in [('2025',100), ('2026',110)]:
                rows[f'{year}-{month}'] = dict(complete_month=True, working_days=20, mw={'x':v})
        self.assertTrue(classify(rows, '2026-08', 'x', self.rules)['persistent'])
        rows['2026-07']['mw']['x'] = 90
        self.assertFalse(classify(rows, '2026-08', 'x', self.rules)['persistent'])
        del rows['2026-07']
        result = classify(rows, '2026-08', 'x', self.rules)
        self.assertFalse(result['persistence_evaluable'])
        self.assertEqual(result['status'], 'observar')

    def test_no_future_month_dependency_and_calendar_flag(self):
        rows = self.sample()
        before = classify(rows, '2026-08', 'x', self.rules)
        rows['2026-09'] = dict(complete_month=True, working_days=100, mw={'x':99999})
        self.assertEqual(before, classify(rows, '2026-08', 'x', self.rules))
        rows['2026-08']['working_days'] = 22
        self.assertTrue(classify(rows, '2026-08', 'x', self.rules)['calendar_review'])
        self.assertEqual(shift('2026-01', -1), '2025-12')

    @unittest.skipUnless(shutil.which('pdftotext'), 'PDF source re-extraction requires Poppler pdftotext')
    def test_pdf_comparison_and_independent_sheets(self):
        d = discrepancies(self.daily, self.monthly)
        saved = json.loads((ROOT/'reports/research/discrepancias-cammesa.json').read_text())
        self.assertEqual(d, saved)
        total = next(r for r in d['rows'] if r['id']=='total')
        self.assertAlmostEqual(total['pdf24_minus_daily_mw'], 3.159852150537536)
        self.assertGreater(total['pdf24_minus_daily_mw'], d['rounding_max_mw_for_15_components_plus_total'])
        self.assertFalse(next(r for r in d['rows'] if r['id']=='aluar')['exceeds_single_value_rounding'])
        self.assertTrue(all(c['daily_count']==1727 and c['maximum_absolute_difference_mw']<1e-6 for c in d['cross_sheet_checks']))
        leaves = [r for r in d['rows'] if r['id'] in [a['id'] for a in self.labels]+['aluar']]
        self.assertAlmostEqual(sum(r['pdf_revision_mw'] for r in leaves), 2.1)

    def test_saved_alerts_and_no_deployment(self):
        result = alert_report(self.monthly, self.labels, self.rules)
        self.assertEqual(result, json.loads((ROOT/'reports/research/alertas-sectoriales.json').read_text()))
        self.assertEqual(len(result['rows']), 14)
        self.assertEqual(sum(r['status']=='prioridad' for r in result['rows']), 6)
        self.assertFalse(result['rules']['notification_enabled'])
        self.assertEqual(result['partial_periods'], ['2026-09'])
        self.assertEqual(result['period'], '2026-08')

    def test_contributions_reconcile_without_double_counting(self):
        result = alert_report(self.monthly, self.labels, self.rules)
        lookup = {r['period']:r for r in self.monthly}
        for branch in ['food_commerce_services','industry','oil_minerals']:
            contribution = sum(r['branch_contribution_pp'] for r in result['rows'] if r['branch']==branch)
            expected = 100*(lookup['2026-08']['mw'][branch]/lookup['2025-08']['mw'][branch]-1)
            self.assertAlmostEqual(contribution, expected)


if __name__ == '__main__':
    unittest.main()
