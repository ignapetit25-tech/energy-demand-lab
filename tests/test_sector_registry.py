"""Synthetic prospective scenarios stay in memory; never populate the real ledger."""
import copy
import json
import unittest
from datetime import datetime,timezone
from unittest.mock import patch
from scripts import sector_registry as s
from scripts.monthly_sector_review import inputs,review,markdown_section


def clock(text):return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.p=s.verified_protocol();self.l=s.empty_ledger(self.p)
        self.now=clock('2026-11-05T12:00:00')
        self.monthly={r['period']:r for r in json.loads((s.ROOT/'data/activity_monthly_history.json').read_text())['monthly']}
        self.rules=json.loads((s.ROOT/'data/sector_alert_rules.json').read_text())

    def record(self,p='2026-10',pub='2026-12-08',capture='2026-12-08T12:00:00Z',value=5):
        return dict(period=p,published_at=pub,captured_at=capture,reviewed=True,reviewer='Synthetic test only',source_url='https://www.indec.gob.ar/test.pdf',latest_known_attestation=True,
                    observations={k:dict(code=c,yoy_percent=value,locator='test cell') for k,c in self.p['indec_codes'].items()})

    def signal(self,baseline=True):
        # Shift existing monthly shapes to the synthetic target; no filesystem writes.
        m={s.shift(k,2):copy.deepcopy(v) for k,v in self.monthly.items()}
        b=self.record('2026-08','2026-10-08','2026-10-08T12:00:00Z',-5) if baseline else None
        return s.issue(self.l,'2026-10',m,b,dict(captured_at='2026-11-05T10:00:00Z'),self.p,self.rules,self.now)

    def publish(self,when='2026-11-05T13:00:00'):
        return s.publication(self.l,'2026-10','a'*40,copy.deepcopy(self.l),{},self.p,clock(when))

    def result(self,record=None):
        return s.outcome(self.l,'2026-10',record or self.record(),self.p,clock('2026-12-09T12:00:00'))

    def test_empty_is_pending_not_zero(self):
        a=s.assess(self.l,self.p,self.now)
        self.assertIsNone(a['primary_metrics']);self.assertEqual(a['decision'],'pendiente');self.assertEqual(len(a['months']),12)
        real=json.loads((s.ROOT/s.LEDGER).read_text());s.validate_chain(real,self.p,s.ROOT)

    def test_neutral_band_inclusive(self):
        self.assertEqual([s.sign(x) for x in [-.5001,-.5,0,.5,.5001]],[-1,0,0,0,1])

    def test_no_premature_or_outside_issuance(self):
        with self.assertRaises(ValueError):s.closed('2026-10',clock('2026-10-31T23:59:00'))
        with self.assertRaises(ValueError):s.period_check('2026-09',self.p)

    def test_issue_once_and_hash_tamper(self):
        self.signal();s.validate_chain(self.l,self.p)
        with self.assertRaises(ValueError):self.signal()
        self.l['events'][0]['payload']['rows'][0]['yoy_percent']=999
        with self.assertRaises(ValueError):s.validate_chain(self.l,self.p)

    def test_publication_requires_identical_public_event(self):
        self.signal()
        with self.assertRaises(ValueError):s.publication(self.l,'2026-10','a'*40,s.empty_ledger(self.p),{},self.p,self.now)
        self.publish()
        with self.assertRaises(ValueError):self.publish()

    def test_timely_paired_assessment(self):
        self.signal();self.publish();self.result()
        a=s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))
        self.assertEqual(a['eligible_pairs'],3);self.assertEqual(a['decision'],'pendiente')

    def test_no_publication_no_eligibility(self):
        self.signal();self.result()
        a=s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))
        self.assertEqual(a['eligible_pairs'],0);self.assertEqual(a['rows'][0]['exclusion_reason'],'emision_no_verificable')

    def test_date_only_same_day_is_late(self):
        self.signal();self.publish('2026-12-08T01:00:00');self.result()
        a=s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))
        self.assertEqual(a['rows'][0]['exclusion_reason'],'emision_tardia')

    def test_missing_baseline_is_not_imputed(self):
        self.signal(False);self.publish();self.result()
        a=s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))
        self.assertEqual(a['rows'][0]['exclusion_reason'],'sin_comparador_archivado')

    def test_revision_never_replaces_first_result(self):
        self.signal();self.publish();self.result()
        before=s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))['rows']
        self.assertIsNone(self.result())
        revised=self.record(capture='2026-12-09T11:00:00Z',value=-5)
        self.assertEqual(self.result(revised)['kind'],'revision')
        self.assertEqual(before,s.assess(self.l,self.p,clock('2026-12-09T13:00:00'))['rows'])
        with self.assertRaises(ValueError):self.result(self.record(value=-2))

    def test_bad_ipi_and_future_capture(self):
        for change in [dict(reviewed=False),dict(captured_at='2027-01-01T00:00:00Z'),dict(source_url='https://example.com/a')]:
            r=self.record();r.update(change)
            with self.assertRaises(ValueError):s.reviewed_ipi(r,clock('2026-12-09T00:00:00'),self.p)
        r=self.record();r['observations']['metals']['yoy_percent']=float('nan')
        with self.assertRaises(ValueError):s.reviewed_ipi(r,clock('2026-12-09T00:00:00'),self.p)

    def test_real_archive_parser_and_complete_month_guards(self):
        raw=(s.ROOT/s.SOURCE).read_bytes();p=dict(self.p,start_period='2026-08')
        m=s.monthly_source(raw,'2026-09-25T12:00:00Z',clock('2026-09-26T12:00:00'),'2026-08',p)
        self.assertEqual(m['2026-08']['mw'],self.monthly['2026-08']['mw'])
        with self.assertRaises(ValueError):s.monthly_source(raw,'2026-09-25T12:00:00Z',self.now,'2026-10',self.p)
        rows,header=s.read_zip(raw);rows[1]['date']=rows[0]['date']
        with patch.object(s,'read_zip',return_value=(rows,header)):
            with self.assertRaises(ValueError):s.monthly_source(raw,'2026-09-25T12:00:00Z',clock('2026-09-26T12:00:00'),'2026-08',p)

    def test_closed_bootstrap_and_exclusion_cannot_erase(self):
        for i in range(12):
            p=s.shift('2026-10',i);t=clock(s.shift(p,1)+'-05T12:00:00')
            baseline=self.record(s.shift(p,-1),s.shift(p,1)+'-01',s.shift(p,1)+'-01T12:00:00Z',-5)
            s.append(self.l,'issue',p,dict(rows=[dict(id=k,status='prioridad',yoy_percent=5) for k in self.p['activity_ids']],baseline=baseline),t)
            s.append(self.l,'publication',p,dict(verified_public_at=s.stamp(t)),t)
            record=self.record(p,s.shift(p,1)+'-08',s.shift(p,1)+'-08T12:00:00Z',5)
            s.append(self.l,'outcome',p,dict(record=record),clock(s.shift(p,1)+'-09T12:00:00'))
        s.append(self.l,'exclusion','2026-10',dict(reason='Cannot erase valid result'),clock('2027-10-10T00:00:00'))
        a=s.assess(self.l,self.p,clock('2027-10-10T00:00:00'))
        self.assertEqual(a['priority_pairs'],36);self.assertEqual(a['decision'],'favorable_limitada');self.assertEqual(a['interval_95_pp'],[100,100])
        self.assertEqual(a,s.assess(self.l,self.p,clock('2027-10-10T00:00:00')))


class IntegrationTests(unittest.TestCase):
    def test_months_not_substituted(self):
        d=inputs();aug=review('2026-08-01',d);jul=review('2026-07-01',d);old=review('2022-01-01',d)
        self.assertEqual(len(aug['rows']),14);self.assertEqual(aug['production'],[])
        self.assertEqual(len(jul['production']),3);self.assertEqual(old['rows'],[])
        self.assertIn('Registro prospectivo','\n'.join(markdown_section(dict(sector_review=aug))))

    def test_metals_counts_sources_and_vintages(self):
        from scripts.investigate_metals import build
        d=build();self.assertEqual(d['summary']['opposite'],15);self.assertEqual(d['summary']['pairs'],43)
        self.assertEqual(d['summary']['opposite_after_median'],13);self.assertEqual(d['summary']['opposite_after_working_mean'],14)
        a=d['april_case'];self.assertAlmostEqual(sum(r['contribution_pp'] for r in a['subgroups']),-1.4)
        self.assertNotEqual(a['first_report_ipi_yoy_percent'],a['revised_snapshot_ipi_yoy_percent'])
        self.assertEqual(d,json.loads((s.ROOT/'reports/research/divergencias-metales.json').read_text()))
