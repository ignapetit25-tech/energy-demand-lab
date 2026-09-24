import copy
import csv
import unittest

from scripts.build_monthly_reports import ROOT, SECTORS, make_report, validate


class MonthlyReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'data/raw/electricity_demand_sectors_monthly.csv').open() as f:
            cls.rows=[{k:(v if k=='period' else float(v)) for k,v in r.items()} for r in csv.DictReader(f)]

    def test_august_changes_reconcile(self):
        validate(self.rows)
        r=make_report(self.rows,'2026-08-01')
        self.assertAlmostEqual(r['total']['delta_gwh'],713.271376,places=5)
        self.assertAlmostEqual(sum(s['contribution_pp'] for s in r['sectors']),r['total']['yoy_percent'],places=6)
        self.assertAlmostEqual(sum(s['share_percent'] for s in r['sectors']),100,places=6)
        self.assertGreater(r['sectors'][0]['delta_gwh'],0)
        self.assertLess(r['sectors'][1]['delta_gwh'],0)
        self.assertEqual(r['ytd']['months'],8)
        self.assertAlmostEqual(r['ytd']['current_gwh'],sum(x['total_gwh'] for x in self.rows if x['period'].startswith('2026-')),places=6)

    def test_missing_ytd_month_is_not_silently_summed(self):
        rows=[r for r in self.rows if r['period']!='2025-02-01']
        self.assertIsNone(make_report(rows,'2026-08-01')['ytd'])

    def test_cancelling_changes_have_finite_contributions(self):
        rows=[dict(period='2025-08-01',total_gwh=100,residential_gwh=50,commerce_industry_gwh=30,large_users_gwh=20),
              dict(period='2026-08-01',total_gwh=100,residential_gwh=60,commerce_industry_gwh=20,large_users_gwh=20)]
        validate(rows)
        r=make_report(rows,'2026-08-01')
        self.assertEqual(r['total']['delta_gwh'],0)
        self.assertEqual([s['contribution_pp'] for s in r['sectors']],[10,-10,0])

    def test_zero_sector_base_does_not_create_infinite_growth(self):
        rows=[dict(period='2025-08-01',total_gwh=100,residential_gwh=80,commerce_industry_gwh=20,large_users_gwh=0),
              dict(period='2026-08-01',total_gwh=110,residential_gwh=80,commerce_industry_gwh=20,large_users_gwh=10)]
        validate(rows)
        self.assertIsNone(make_report(rows,'2026-08-01')['sectors'][2]['yoy_percent'])

    def test_invalid_or_duplicate_data_is_rejected(self):
        with self.assertRaises(ValueError):
            validate(self.rows+[self.rows[-1]])
        bad=copy.deepcopy(self.rows)
        bad[-1]['total_gwh']+=1
        with self.assertRaises(ValueError):
            validate(bad)
        bad[-1]['total_gwh']=float('nan')
        with self.assertRaises(ValueError):
            validate(bad)


if __name__=='__main__':
    unittest.main()
