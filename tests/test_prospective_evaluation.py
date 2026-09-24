import copy
import csv
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from scripts import evaluate_prospective as engine
from scripts.evaluate_prospective import evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.forecasts=[dict(target_period='2026-10-01',issue_timestamp='2026-09-20T23:44:41-03:00',
                            primary_adaptive_annual_change_gwh='10578.252',seasonal_naive_gwh='10591.336',
                            fixed_60m_annual_change_gwh='10706.834',seasonal_naive_expanding_drift_gwh='10809.74')]
        self.outcome=dict(target_period='2026-10-01',actual_gwh=10000,captured_at='2026-11-15T10:00:00+00:00',
                          publication_date=None,source_url='https://apis.datos.gob.ar/series/api/series/',source_sha256='test-only')
        self.now=datetime(2026,11,16,tzinfo=timezone.utc)

    def test_pending_is_not_zero(self):
        r=evaluate(self.forecasts,[],self.now)
        self.assertEqual(r['pending_months'],1)
        self.assertIsNone(r['metrics']['overall']['models']['primary'])
        self.assertIsNone(r['records'][0]['errors'])

    def test_signed_errors_and_paired_difference(self):
        r=evaluate(self.forecasts,[self.outcome],self.now)
        self.assertAlmostEqual(r['metrics']['overall']['models']['primary']['mae_gwh'],578.252)
        self.assertAlmostEqual(r['records'][0]['benchmark_minus_primary_absolute_gwh'],13.084)
        self.assertEqual(r['metrics']['shoulder']['months'],1)
        self.outcome['actual_gwh']=12000
        r=evaluate(self.forecasts,[self.outcome],self.now)
        self.assertLess(r['records'][0]['errors']['primary']['signed_gwh'],0)
        self.assertGreater(r['records'][0]['errors']['primary']['absolute_gwh'],0)

    def test_rejects_early_capture_and_future_capture(self):
        for capture in ['2026-10-31T10:00:00+00:00','2026-12-01T00:00:00+00:00','2026-11-15T10:00:00']:
            with self.subTest(capture=capture):
                self.outcome['captured_at']=capture
                with self.assertRaises(ValueError): evaluate(self.forecasts,[self.outcome],self.now)

    def test_rejects_duplicates_and_invalid_observations(self):
        with self.assertRaises(ValueError):evaluate(self.forecasts,[self.outcome,self.outcome],self.now)
        for value in [0,-1,float('nan'),float('inf')]:
            self.outcome['actual_gwh']=value
            with self.assertRaises(ValueError):evaluate(self.forecasts,[self.outcome],self.now)

    def test_rejects_late_forecast_and_invalid_publication_date(self):
        f=copy.deepcopy(self.forecasts);f[0]['issue_timestamp']='2026-10-01T00:00:00+00:00'
        with self.assertRaises(ValueError):evaluate(f,[self.outcome],self.now)
        self.outcome['publication_date']='2026-10-30'
        with self.assertRaises(ValueError):evaluate(self.forecasts,[self.outcome],self.now)

    def test_snapshot_recording_is_idempotent_and_revisions_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'prospective').mkdir();(root/'dashboard').mkdir()
            f=copy.deepcopy(self.forecasts[0]);f['target_period']='2025-08-01';f['issue_timestamp']='2025-07-20T00:00:00+00:00'
            with (root/'prospective/forecasts.csv').open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=f.keys());writer.writeheader();writer.writerow(f)
            ledger=root/'prospective/outcomes.json';ledger.write_text('[]')
            source=root/'source.csv';source.write_text('indice_tiempo,demanda_total\n2025-08-01,10000\n')
            with patch.object(engine,'ROOT',root):
                result=engine.record_snapshot(source,'2025-09-15T00:00:00+00:00','https://apis.datos.gob.ar/series/api/series/')
                self.assertEqual(result['evaluated_months'],1)
                saved=ledger.read_bytes()
                engine.record_snapshot(source,'2025-09-16T00:00:00+00:00','https://apis.datos.gob.ar/series/api/series/')
                self.assertEqual(ledger.read_bytes(),saved)
                source.write_text('indice_tiempo,demanda_total\n2025-08-01,10001\n')
                with self.assertRaises(ValueError):
                    engine.record_snapshot(source,'2025-09-17T00:00:00+00:00','https://apis.datos.gob.ar/series/api/series/')
                self.assertEqual(ledger.read_bytes(),saved)
                snapshot=root/json.loads(saved)[0]['snapshot_file'];snapshot.write_text('changed')
                with self.assertRaises(ValueError):engine.build()
