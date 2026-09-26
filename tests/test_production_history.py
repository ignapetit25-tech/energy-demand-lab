import copy
import hashlib
import json
import unittest
from pathlib import Path
from scripts.build_production_history import build
from scripts.analyze_sector_followups import shift

ROOT=Path(__file__).resolve().parents[1]


class ProductionHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads((ROOT/'data/production_history_source.json').read_text())
        cls.electricity=json.loads((ROOT/'data/activity_monthly_history.json').read_text())
        cls.result=build(cls.raw,cls.electricity)

    def test_coverage_source_and_reproducibility(self):
        d=self.result
        self.assertEqual(d,json.loads((ROOT/'data/production_history.json').read_text()))
        self.assertEqual(len(self.raw['observations']),381)
        self.assertEqual(len(d['comparisons']),129)
        self.assertEqual(len(d['periods']),43)
        self.assertEqual((d['periods'][0],d['periods'][-1]),('2023-01','2026-07'))
        self.assertNotIn('2026-08',d['periods'])
        for r in self.raw['observations']:
            self.assertRegex(r['original_index_cell'],r'^Cuadro 2![A-Z]+[0-9]+$')
            self.assertRegex(r['yoy_percent_cell'],r'^Cuadro 3![A-Z]+[0-9]+$')

    def test_july_pdf_rounding_and_historical_counts(self):
        pdf=json.loads((ROOT/'data/physical_production_evidence.json').read_text())
        for p in pdf['observations']:
            r=next(r for r in self.result['comparisons'] if r['period']=='2026-07' and r['activity_id']==p['electricity_activity_id'])
            self.assertEqual(round(r['yoy_percent'],1),p['yoy_percent'])
            self.assertEqual(round(r['original_index'],1),p['original_index_base_2004'])
        self.assertEqual([r['matching_direction'] for r in self.result['summary']],[37,28,36])

    def test_no_period_substitution_or_missing_rates_to_zero(self):
        self.assertTrue(all(r['yoy_percent'] is None for r in self.raw['observations'] if r['period']<'2017-01'))
        source={(r['period'],r['activity_id']):r for r in self.raw['observations']}
        for r in self.result['comparisons']:
            self.assertEqual(r['yoy_percent'],source[(r['period'],r['activity_id'])]['yoy_percent'])
            self.assertAlmostEqual(r['electricity_yoy_percent'],100*(r['electricity_current_mw']/r['electricity_previous_mw']-1))

    def test_reject_duplicates_bad_indices_and_inconsistent_rates(self):
        for mutation in ['duplicate','rate','index']:
            raw=copy.deepcopy(self.raw)
            if mutation=='duplicate':raw['observations'].append(raw['observations'][-1])
            elif mutation=='rate':raw['observations'][-1]['yoy_percent']+=1
            else:raw['observations'][-1]['original_index']=0
            with self.assertRaises(ValueError):build(raw,self.electricity)

    def test_future_protocol_frozen_separate_and_pending(self):
        p=json.loads((ROOT/'prospective/sector-alerts-protocol.json').read_text())
        self.assertEqual(p['start_period'],'2026-10')
        self.assertEqual(shift(p['start_period'],p['months']-1),p['end_period'])
        self.assertGreater(p['start_period'],p['designed_at'][:7])
        self.assertEqual(set(p['activity_ids']),{'construction','metals','textiles'})
        for file,digest in p['frozen_inputs'].items():
            self.assertEqual(hashlib.sha256((ROOT/file).read_bytes()).hexdigest(),digest)
        self.assertEqual(p['signals'],[]);self.assertEqual(p['outcomes'],[])
        self.assertIsNone(p['primary_metrics']);self.assertFalse(p['automatic_refresh'])


if __name__=='__main__':unittest.main()
