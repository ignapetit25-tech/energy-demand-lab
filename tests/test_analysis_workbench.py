import copy
import json
import unittest
from datetime import date
from scripts.analysis_workbench import build,executive,operational_check,text_section
from scripts.monthly_sector_review import inputs,review
from scripts.document_review import reference,package,evaluate,compare


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=inputs()

    def test_priority_order_not_confidence(self):
        r=review('2026-08-01',self.data);e=executive(dict(summary='test'),r)
        expected=sorted([x for x in r['rows'] if x['status']=='prioridad'],key=lambda x:(-abs(x['delta_mw']),x['id']))[:3]
        self.assertEqual([x['id'] for x in e['findings']],[x['id'] for x in expected])
        self.assertNotIn('confidence',json.dumps(e));self.assertEqual(len(e['findings']),3)

    def test_all_alerts_have_separate_quality(self):
        for period in self.data['alerts']['periods']:
            r=review(period,self.data)
            self.assertEqual(len(r['rows']),14)
            self.assertTrue(all(x['quality'] for x in r['rows']))
            for x in r['rows']:self.assertEqual(x['status'],next(a['status'] for a in self.data['alerts']['baseline'][period]['rows'] if a['id']==x['id']))

    def test_missing_month_and_partial_mapping(self):
        aug=review('2026-08',self.data);july=review('2026-07',self.data)
        self.assertEqual(next(x['quality'] for x in aug['rows'] if x['id']=='metals'),'IPI del mismo mes ausente')
        self.assertIn('Proxy parcial',next(x['quality'] for x in july['rows'] if x['id']=='construction'))
        self.assertEqual(executive(dict(summary='test'),review('2022-01',self.data))['findings'],[])
        early=executive(dict(summary='test'),review('2023-01',self.data))
        self.assertTrue(early['findings']);self.assertTrue(all(f['persistent'] is None for f in early['findings']))

    def test_source_dates_are_not_invented(self):
        w=build(self.data,date(2026,9,26))
        self.assertTrue(all(s['published_at'] is None for s in w['sources']))
        self.assertEqual(w['partial_periods'],['2026-09'])
        self.assertEqual(w['document_assistant']['real_runs'],0)
        self.assertIsNone(w['document_assistant']['measured_accuracy'])

    def test_operation_before_after_close_and_already_issued(self):
        registry=copy.deepcopy(self.data['registry'])
        before=operational_check(registry,'2026-08',date(2026,9,26))
        self.assertEqual(before['state'],'Aún no corresponde emitir')
        self.assertIn('2026-11-01',before['steps'][0])
        after=operational_check(registry,'2026-08',date(2026,11,1))
        self.assertEqual(after['state'],'Revisión manual requerida');self.assertFalse(after['automatic'])
        registry['months'][0]['issued']=True;registry['months'][0]['status']='pendiente_de_resultado'
        issued=operational_check(registry,'2026-10',date(2026,11,5))
        self.assertFalse(any('Emitir una sola vez' in x for x in issued['steps']))
        self.assertTrue(any('primera observación' in x for x in issued['steps']))

    def test_casebook_is_data_driven_and_cautious(self):
        d=copy.deepcopy(self.data);d['metals']['summary']['opposite']=12
        w=build(d,date(2026,9,26));self.assertIn('12 de 43',w['metals']['narrative'])
        self.assertEqual(len(w['metals']['casebook']['hypotheses']),4)
        self.assertTrue(all(h['counter'] and h['needed'] and h['source_url'].startswith('https://') for h in w['metals']['casebook']['hypotheses']))
        text='\n'.join(text_section(executive(dict(summary='test'),review('2026-08',d)),w))
        self.assertIn('Sin modelo conectado',text)


class DocumentaryTests(unittest.TestCase):
    def test_package_omits_answers_and_has_no_measurement(self):
        p=package();self.assertEqual(len(p['tasks']),7)
        self.assertTrue(all('value' not in x for x in p['tasks']));self.assertIsNone(p['accuracy'])

    def test_perfect_synthetic_is_not_automatic_approval(self):
        result=evaluate(reference())
        self.assertEqual(result['counts']['correct'],7);self.assertEqual(result['exact_fraction'],1)
        self.assertFalse(result['automatic_import_allowed']);self.assertTrue(result['human_review_required'])

    def test_wrong_unit_period_citation_or_revision_fails(self):
        for field,value in [('unit','GWh'),('period','2026-07'),('page',18),('source_sha256','bad'),('value',-1.48)]:
            candidate=reference();candidate['items'][0][field]=value
            self.assertEqual(evaluate(candidate)['counts']['incorrect'],1)

    def test_missing_abstention_extra_and_duplicate(self):
        c=reference();c['items'].pop();c['items'][0]['value']=None
        c['items'].append(dict(id='invented',value=999))
        r=evaluate(c);self.assertEqual(r['counts']['missing'],1);self.assertEqual(r['counts']['abstained'],1);self.assertEqual(r['extra_ids'],['invented'])
        c['items'].append(c['items'][0])
        with self.assertRaises(ValueError):evaluate(c)

    def test_invalid_numbers_rejected(self):
        for value in [True,float('nan'),float('inf'),'3.5']:
            c=reference();c['items'][0]['value']=value
            with self.assertRaises(ValueError):evaluate(c)

    def test_compare_keeps_versions(self):
        a=reference();b=copy.deepcopy(a);b['items'][0]['value']=-1.48
        result=compare(a,b);self.assertEqual(len(result['changes']),1)
        self.assertEqual(result['changes'][0]['before']['value'],-1.4)
        self.assertEqual(a['items'][0]['value'],-1.4)
