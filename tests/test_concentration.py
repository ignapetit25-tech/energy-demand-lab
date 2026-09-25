import copy
import json
import unittest
from pathlib import Path

from scripts.build_concentration import derive, net_share, validate_evidence

ROOT = Path(__file__).resolve().parents[1]


class ConcentrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = json.loads((ROOT/'data/concentration_evidence.json').read_text())
        report = json.loads((ROOT/'reports/monthly/2026-08.json').read_text())
        history = json.loads((ROOT/'data/sector_history.json').read_text())
        source = json.loads((ROOT/'data/sector_source_manifest.json').read_text())
        cls.d = derive([report], source, history, cls.e)

    def test_national_contributions(self):
        c=self.d['national']['comparisons']
        self.assertAlmostEqual(c['month']['rows'][0]['net_growth_share_percent'],69.389489,places=5)
        self.assertAlmostEqual(c['ytd']['rows'][2]['net_growth_share_percent'],99.8167,places=3)
        for x in c.values():
            self.assertAlmostEqual(sum(r['net_growth_share_percent'] for r in x['rows']),100)
            self.assertAlmostEqual(sum(r['contribution_pp'] for r in x['rows']),x['total']['yoy_percent'])

    def test_branch_denominators_and_rounding(self):
        periods=self.d['branch_comparisons']
        self.assertEqual(len(periods),12)
        latest=periods[-1]; a=next(r for r in latest['rows'] if r['id']=='aluar')
        self.assertEqual(a['delta_mw'],171)
        self.assertEqual(latest['total_delta_mw'],131)
        self.assertAlmostEqual(a['net_growth_share_percent'],130.534351,places=5)
        self.assertAlmostEqual(a['current_share_percent'],13.85863,places=4)
        self.assertIsNone(net_share(100,0)); self.assertIsNone(net_share(100,-10))
        for p in periods:
            self.assertEqual(sum(r['delta_mw'] for r in p['rows'])+p['rounding_residual_mw'],p['total_delta_mw'])
            if p['total_delta_mw']<=0:
                self.assertTrue(all(r['net_growth_share_percent'] is None for r in p['rows']))

    def test_annual_balance_and_non_attribution(self):
        rows={r['id']:r for r in self.d['aluar_annual_comparison']}
        self.assertAlmostEqual(rows['production_tonnes']['change_percent'],1.201364,places=5)
        self.assertAlmostEqual(rows['electricity_mwh']['change_percent'],1.683607,places=5)
        self.assertAlmostEqual(rows['grid_contract_mwh']['change_percent'],8.485096,places=5)
        previous,current=self.e['aluar']['observations']
        delta=sum(rows[k]['delta'] for k in ('grid_contract_mwh','thermal_self_supply_mwh','wind_self_supply_mwh'))
        self.assertEqual(delta+current['unreconciled_mwh']-previous['unreconciled_mwh'],112918)
        self.assertTrue(all(v is None for k,v in self.e['aluar']['monthly_attribution'].items() if k.endswith('_percent')))

    def test_activity_windows_and_persistence(self):
        g=self.e['gumas']; self.assertEqual(len(g['activities']),14)
        self.assertEqual([p['days'] for p in g['periods']],[31,16])
        self.assertEqual(g['matched_september']['days_each'],16)
        self.assertTrue(all(r['published_yoy_percent']>0 for r in g['matched_september']['rows']))
        self.assertEqual(len(self.d['indec_persistence']),12)
        self.assertTrue(all(r['comparisons']==7 for r in self.d['indec_persistence']))
        self.assertEqual(sum(r['up']==0 for r in self.d['indec_persistence']),3)

    def test_invalid_evidence_is_rejected(self):
        mutations=[
            lambda e:e['sources'][0].update(sha256='0'*64),
            lambda e:e['sources'][0].update(document_date='2027-01-01'),
            lambda e:e['aluar']['observations'][0].update(unreconciled_mwh=0),
            lambda e:e['aluar']['monthly_attribution'].update(ai_share_percent=0),
            lambda e:e['gumas']['periods'][1].update(complete_month=True),
            lambda e:e['gumas']['activities'][0]['values'].update({'2026-08':1000}),
            lambda e:e['gumas']['matched_september'].update(previous_end='2025-09-30'),
            lambda e:e['gumas']['matched_september']['rows'].pop(),
            lambda e:e['gumas']['matched_september']['rows'][0].update(published_delta_mw=float('nan')),
        ]
        for mutate in mutations:
            e=copy.deepcopy(self.e); mutate(e)
            with self.assertRaises(ValueError): validate_evidence(e)


if __name__=='__main__': unittest.main()
