import unittest
from datetime import datetime, timezone
from observatory.fixture import FIELDS, generate
from observatory.pipeline import model, records, ordered_stage, funnel_records, retention, analyze, DAY
from observatory.stats import wilson, difference, sample_size

BASE=int(datetime(2020,11,1,tzinfo=timezone.utc).timestamp()*1e6)
def event(name,seconds=0,user='u',session=1,order=None,revenue=None):
    return dict(zip(FIELDS,['20201101',BASE+int(seconds*1e6),name,user,session,1,'mobile','google','organic',order,revenue,revenue,'USD',revenue]))
def modeled(rows):
    con=model(rows); return records(con,'events'),records(con,'purchases')

class AnalysisTests(unittest.TestCase):
    def test_session_key_includes_user_and_preserves_cross_midnight(self):
        rows=[event('view_item',86399,'a',7),event('add_to_cart',86401,'a',7),event('view_item',0,'b',7)]
        c=model(rows); ss=records(c,'sessions')
        self.assertEqual(len(ss),2)
        self.assertEqual(next(s['event_count'] for s in ss if s['user_key']=='a'),2)

    def test_missing_identifiers_never_merge(self):
        es,ps=modeled([event('view_item',user=None),event('view_item',session=None),event('view_item',user='<Other>')])
        self.assertTrue(all(e['session_key'] is None for e in es))
        self.assertEqual(sum(e['user_key'] is not None for e in es),1)

    def test_duplicate_session_parameter_quarantined(self):
        r=event('view_item'); r['session_param_count']=2
        es,_=modeled([r]); self.assertIsNone(es[0]['session_key'])

    def test_out_of_order_and_ties_do_not_convert(self):
        es,_=modeled([event('purchase',0,order='x'),event('view_item',1),event('add_to_cart',1),event('begin_checkout',3)])
        self.assertEqual(ordered_stage(es)[0],1)

    def test_ordered_path_recovers_after_early_invalid_events(self):
        es,_=modeled([event('add_to_cart',0),event('view_item',1),event('begin_checkout',2),event('add_to_cart',3),event('begin_checkout',4),event('purchase',5,order='x')])
        self.assertEqual(ordered_stage(es)[0],4)

    def test_cross_session_and_conversion_window(self):
        rows=[event('view_item'),event('add_to_cart',1),event('begin_checkout',86400,session=2),event('purchase',86401,session=2,order='x')]
        es,ps=modeled(rows); sr,ur,_=funnel_records(es,ps,BASE+8*DAY)
        self.assertEqual(max(r['stage'] for r in sr),2)
        self.assertEqual(ur[0]['stage'],4)
        rows[-1]['event_timestamp']=BASE+7*DAY
        es,ps=modeled(rows); _,ur,_=funnel_records(es,ps,BASE+8*DAY)
        self.assertEqual(ur[0]['stage'],3)

    def test_no_view_excluded_from_denominator_and_immature_removed(self):
        es,ps=modeled([event('purchase',order='x'),event('view_item',user='v')])
        sr,ur,im=funnel_records(es,ps,BASE+6*DAY)
        self.assertEqual(sum(r['stage']>0 for r in sr),1)
        self.assertEqual(ur,[]); self.assertEqual(im,1)

    def test_purchase_dedup_is_global_and_missing_orders_excluded(self):
        es,ps=modeled([event('purchase',1,order='x',revenue=10),event('purchase',2,user='v',order='x',revenue=20),event('purchase',3)])
        self.assertEqual(len(ps),1); self.assertEqual(ps[0]['revenue_usd'],10)

    def test_cohort_full_followup_and_new_session(self):
        rows=[event('view_item',86400),event('page_view',2*86400),event('page_view',3*86400,session=2),event('view_item',2*86400,user='v')]
        es,ps=modeled(rows)
        cells,_=retention(es,ps,BASE+9*DAY)
        self.assertFalse(cells[0]['eligible'])
        cells,_=retention(es,ps,BASE+10*DAY)
        self.assertTrue(cells[0]['eligible']); self.assertEqual(cells[0]['k'],1); self.assertEqual(cells[0]['n'],2)

    def test_repeat_purchase_requires_distinct_order_and_full_followup(self):
        es,ps=modeled([event('purchase',order='x'),event('purchase',86400,order='x'),event('purchase',2*86400,order='y'),event('purchase',29*86400,user='v',order='z')])
        _,repeat=retention(es,ps,BASE+30*DAY)
        self.assertEqual((repeat['k'],repeat['n']),(1,1))

    def test_reconciliation_and_filter_partitions(self):
        d=analyze(generate(70),'synthetic fixture'); q=d['quality']
        self.assertEqual(q['source_counts'],q['model_counts'])
        self.assertEqual(q['raw_purchases'],q['canonical_purchases']+q['duplicate_purchases']+q['missing_transaction'])
        for mode in ['session','user']:
            total=next(f for f in d['funnels'] if f['mode']==mode and f['device']=='All' and f['channel']=='All')
            parts=[f for f in d['funnels'] if f['mode']==mode and f['device']!='All' and f['channel']=='All']
            self.assertEqual(sum(f['n'] for f in parts),total['n'])
            for f in parts: self.assertEqual(f['counts'],sorted(f['counts'],reverse=True))

    def test_interval_boundaries_and_power_reference(self):
        self.assertEqual(wilson(0,0),[None,None])
        self.assertAlmostEqual(wilson(50,100)[0],.40383153,places=6)
        self.assertLess(difference(10,100,20,100)['estimate'],0)
        self.assertEqual(sample_size()['per_arm'],2402)
        with self.assertRaises(ValueError): sample_size(baseline=.99,absolute_mde=.1)

if __name__=='__main__': unittest.main()
