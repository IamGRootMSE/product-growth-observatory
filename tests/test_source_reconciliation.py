import unittest
from scripts.reconcile_source import reconcile
from test_analysis import event

class SourceReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.rows=[event('purchase',order='x',revenue=20),event('purchase',1,user=None,revenue=10)]
        self.audit=[dict(event_name='purchase',event_count='2',missing_user_count='1',users='1',raw_purchase_revenue_usd='30')]
    def test_independent_aggregate_matches(self):
        self.assertTrue(reconcile(self.rows,self.audit))
    def test_truncated_export_is_rejected(self):
        with self.assertRaises(AssertionError): reconcile(self.rows[:1],self.audit)
    def test_revenue_disagreement_is_rejected(self):
        self.audit[0]['raw_purchase_revenue_usd']='999'
        with self.assertRaises(AssertionError): reconcile(self.rows,self.audit)
