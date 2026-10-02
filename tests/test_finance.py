import copy
from datetime import date
import unittest
from observatory.finance import analyze, bridge, fixture, forecast, model, repeat_cohorts, state


class FinanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orders=fixture()
        cls.result=analyze(cls.orders)

    def test_sql_totals_and_economic_identity(self):
        self.assertEqual(sum(m['orders'] for m in self.result['months']),len(self.orders))
        for m in self.result['months']:
            self.assertAlmostEqual(m['revenue']-m['cost'],m['margin'])

    def test_bridge_hand_calculation_and_support(self):
        a=state([dict(product='a',orders=10,revenue=100,cost=40)])
        b=state([dict(product='a',orders=20,revenue=240,cost=100)])
        r=bridge(a,b)
        self.assertAlmostEqual(r['change'],80)
        self.assertAlmostEqual(r['effects']['volume'],65)
        self.assertAlmostEqual(r['effects']['price'],30)
        self.assertAlmostEqual(r['effects']['cost'],-15)
        self.assertAlmostEqual(r['effects']['mix'],0)
        self.assertAlmostEqual(sum(r['effects'].values()),80)
        self.assertAlmostEqual(bridge(b,a)['change'],-80)
        bad=copy.deepcopy(b);bad['mix']={'new':1}
        with self.assertRaises(ValueError): bridge(a,bad)

    def test_cohort_boundary_and_immaturity(self):
        rows=[dict(customer='a',day='2025-01-01'),dict(customer='a',day='2025-04-01'),
              dict(customer='b',day='2025-01-01'),dict(customer='b',day='2025-03-31'),
              dict(customer='c',day='2025-12-01')]
        result=repeat_cohorts(rows,date(2026,1,1))
        self.assertEqual(result[0]['repeat_buyers'],1)  # day 89 yes; day 90 no
        self.assertEqual(result[0]['buyers'],2)
        self.assertIsNone(result[-1]['rate'])

    def test_holdout_cannot_change_selection_or_earlier_forecasts(self):
        months=copy.deepcopy(self.result['months'])
        original=forecast(months)
        months[23]['revenue']*=100
        changed=forecast(months)
        self.assertEqual(original['selected'],changed['selected'])
        self.assertEqual(original['selection'],changed['selection'])
        for method in original['holdout']:
            self.assertEqual(original['holdout'][method]['points'][-1]['predicted'],
                             changed['holdout'][method]['points'][-1]['predicted'])

    def test_invalid_orders_and_missing_month_rejected(self):
        with self.assertRaises(ValueError): model(self.orders+[self.orders[0]])
        bad=copy.deepcopy(self.orders[:1]);bad[0]['revenue_cents']=float('nan')
        with self.assertRaises(ValueError): model(bad)
        with self.assertRaises(ValueError): forecast(self.result['months'][1:])
        bad=copy.deepcopy(self.result['months']);bad[4]['month']='2024-06'
        with self.assertRaises(ValueError): forecast(bad)


if __name__=='__main__': unittest.main()
