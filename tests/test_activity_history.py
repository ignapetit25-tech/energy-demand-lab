import copy
import json
import unittest
from pathlib import Path
from scripts.build_activity_history import extract,summarize,validate_daily

ROOT=Path(__file__).resolve().parents[1]


class ActivityHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,_=extract();cls.months=summarize(cls.rows)

    def test_coverage_and_partial_month(self):
        self.assertEqual(len(self.rows),1727)
        self.assertEqual(self.rows[0]['date'],'2022-01-01')
        self.assertEqual(self.rows[-1]['date'],'2026-09-23')
        self.assertEqual(sum(r['complete_month'] for r in self.months),56)
        self.assertFalse(self.months[-1]['complete_month'])
        self.assertTrue(all(v is None for v in self.months[-1]['yoy_percent'].values()))
        self.assertEqual(next(r for r in self.months if r['period']=='2024-02')['days'],29)

    def test_aluar_energy_not_gross_consumption(self):
        by={r['period']:r for r in self.months}
        self.assertAlmostEqual(by['2025-08']['aluar_net_grid_gwh'],279.532209)
        self.assertAlmostEqual(by['2026-08']['aluar_net_grid_gwh'],407.095973)
        self.assertAlmostEqual(by['2026-08']['mw']['total'],2292.0401478494623)
        self.assertAlmostEqual(by['2026-08']['yoy_percent']['construction'],-26.40735718,places=6)
        research=json.loads((ROOT/'data/aluar_monthly_research.json').read_text())
        self.assertTrue(all(v is None for v in research['monthly_causal_attribution'].values()))
        self.assertFalse(research['request_sent'])

    def test_missing_and_duplicate_days_rejected(self):
        rows=copy.deepcopy(self.rows[:4]); rows.pop(1)
        with self.assertRaises(ValueError):validate_daily(rows)
        rows=copy.deepcopy(self.rows[:4]);rows[1]['date']=rows[0]['date']
        with self.assertRaises(ValueError):validate_daily(rows)

    def test_subtotals_and_vintage_discrepancy(self):
        rows=copy.deepcopy(self.rows[:4]);rows[0]['mw']['total']+=1
        with self.assertRaises(ValueError):validate_daily(rows)
        d=json.loads((ROOT/'data/activity_monthly_history.json').read_text())
        self.assertEqual(d['monthly'],self.months)
        self.assertEqual(d['revision_comparison']['comparison_pdf_total_mw'],2295.2)
        self.assertNotAlmostEqual(d['revision_comparison']['comparison_pdf_total_mw'],self.months[-2]['mw']['total'],places=1)


if __name__=='__main__':unittest.main()
