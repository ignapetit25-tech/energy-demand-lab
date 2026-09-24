import copy
import unittest
from scripts.build_research import load,validate,validate_history

class ExpandedResearchTests(unittest.TestCase):
    def setUp(self):self.b=load();self.h=self.b['history']

    def test_scope_and_source_boundaries(self):
        h=self.h
        self.assertEqual(len(h['historical_observations']),164)
        self.assertEqual(len(h['monthly_snapshots']),12)
        self.assertEqual(len(h['activity']['observations']),19)
        self.assertEqual(len(h['activity']['sectors']),12)
        self.assertEqual(h['sources'][-1]['coverage_percent'],90)
        self.assertTrue(all(s['coverage_percent']==98 for s in h['sources'][:-1]))
        self.assertFalse(any(r['period']=='2012-09-01' for r in h['historical_observations']))
        august=[r for r in h['historical_observations'] if r['period'][5:7]=='08']
        self.assertEqual(len(august),15)
        self.assertEqual(august[0]['values']['industry'],1982)
        self.assertEqual(august[-1]['values']['industry'],1644)

    def test_published_not_recomputed_rates(self):
        rows={r['id']:r for r in self.h['monthly_snapshots'][-1]['rows']}
        self.assertEqual(rows['without_aluar']['current_mw'],3399)
        self.assertEqual(rows['total']['yoy_percent'],3.4)
        self.assertEqual(rows['aluar']['yoy_percent'],45.6)
        self.assertNotAlmostEqual((547/376-1)*100,45.6,places=2)
        rate=lambda s,k:next(r['yoy_percent'] for r in s['rows'] if r['id']==k)
        self.assertEqual(sum(rate(s,'total')>0 and rate(s,'without_aluar')<0 for s in self.h['monthly_snapshots']),6)

    def test_activity_points_not_percent_growth(self):
        a=self.h['activity']['observations'];now=a[-1];prev=a[6]
        self.assertEqual(now['period'],'2026-07-01')
        self.assertEqual(now['general_percent'],58.2)
        self.assertEqual(now['values']['metalworking'],38.3)
        self.assertEqual(prev['values']['metalworking'],49)
        self.assertAlmostEqual(now['values']['metalworking']-prev['values']['metalworking'],-10.7)
        self.assertEqual(now['values']['refining'],89.9)

    def test_rejects_misdated_mixed_or_invalid_rows(self):
        for mutate in [lambda h:h['historical_observations'].append(h['historical_observations'][0]),
                       lambda h:h['historical_observations'][0].update(source_period='2026-08-01'),
                       lambda h:h['activity']['observations'][0]['values'].update(food=101),
                       lambda h:h['monthly_snapshots'][0]['rows'][0].update(yoy_percent=float('nan'))]:
            h=copy.deepcopy(self.h);mutate(h)
            with self.assertRaises(ValueError):validate_history(h)

    def test_technical_facts_are_not_measured_energy(self):
        r=self.b['registry'];p={p['id']:p for p in r['projects']}
        self.assertEqual(len(p),7)
        self.assertEqual(p['stargate_ar']['announced_power_mw'],500)
        self.assertEqual(p['clementina_xxi']['technical_facts'][0]['value'],233)
        self.assertEqual(p['clementina_xxi']['technical_facts'][0]['unit'],'kW')
        self.assertEqual(p['cirion_bue1']['technical_facts'][0]['qualifier'],'Más de')
        self.assertEqual([f['value'] for f in p['edge_bue01']['technical_facts']],[3.5,10.5])
        self.assertTrue(all(x['measured_energy_gwh'] is None for x in p.values()))
        modified=copy.deepcopy(r);modified['projects'][1]['technical_facts'][0]['source_id']='missing'
        with self.assertRaises(ValueError):validate(modified,self.b['sector'])
