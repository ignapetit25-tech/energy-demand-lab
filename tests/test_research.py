import copy
import unittest

from scripts.build_research import load,validate
from scripts.build_monthly_reports import ROOT
import json


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.bundle=load()

    def test_source_units_and_independent_population(self):
        c=self.bundle['sector']['cammesa']
        self.assertEqual(c['unit'],'MW')
        self.assertEqual(c['period'],'2026-08-01')
        rows={r['id']:r for r in c['rows']}
        self.assertEqual(rows['total']['yoy_percent'],3.4)
        self.assertEqual(rows['without_aluar']['yoy_percent'],-1.2)
        self.assertEqual(rows['industry']['yoy_percent'],-0.7)
        for key in ('current_mw','previous_mw'):
            components=sum(r[key] for r in c['rows'] if r['kind']=='component')
            self.assertLessEqual(abs(components-rows['total'][key]),2)
        self.assertIn('no recalculadas',c['method'])
        self.assertIn('no coincide',c['boundary'])

    def test_unknown_electricity_is_null_and_countries_separate(self):
        projects=self.bundle['registry']['projects']
        self.assertEqual(sum(p['country']=='Argentina' for p in projects),2)
        self.assertTrue(all(p['measured_energy_gwh'] is None for p in projects))
        self.assertEqual(next(p for p in projects if p['id']=='camellia_us')['announced_power_mw'],3200)

    def test_unreferenced_or_undated_measurement_is_rejected(self):
        for updates in ({'measured_energy_gwh':10},{'announced_power_mw':100},{'status_source_ids':['missing']},{'status_as_of':'2099-01-01'}):
            registry=copy.deepcopy(self.bundle['registry'])
            registry['projects'][0].update(updates)
            with self.assertRaises(ValueError):
                validate(registry,self.bundle['sector'])

    def test_no_branch_table_is_backfilled_to_old_month(self):
        bundle=json.loads((ROOT/'dashboard/report-data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
        august=next(r for r in bundle['reports'] if r['period']=='2026-08-01')['text']
        old=next(r for r in bundle['reports'] if r['period']=='2025-08-01')['text']
        self.assertIn('sin Aluar cae 1,2%',august)
        self.assertNotIn('sin Aluar cae 1,2%',old)
        self.assertIn('No se incorporó una tabla por ramas para este mes',old)
        self.assertIn('julio de 2026',august)
        self.assertIn('no agosto',august)

    def test_duplicate_project_and_future_litigation_rejected(self):
        r=copy.deepcopy(self.bundle['registry'])
        r['projects'].append(r['projects'][0])
        with self.assertRaises(ValueError):validate(r,self.bundle['sector'])
        r=copy.deepcopy(self.bundle['registry'])
        r['projects'][-1]['legal_events'][0]['date']='2099-01-01'
        with self.assertRaises(ValueError):validate(r,self.bundle['sector'])
