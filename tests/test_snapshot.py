import unittest
from scripts.check_snapshot import compare


class SnapshotTests(unittest.TestCase):
    def test_roundoff_and_material_or_schema_drift(self):
        compare({'mean':1.0,'count':3}, {'mean':1.0+1e-14,'count':3})
        for expected, actual in [({'mean':1.0},{'mean':1.01}),
                                 ({'count':3},{'count':4}),
                                 ({'count':1},{'count':True}),
                                 ({'a':None},{}),
                                 ([1,2],[1]),
                                 ('last_month','driver_mean3'),
                                 (float('nan'),float('nan'))]:
            with self.subTest(expected=expected), self.assertRaises(AssertionError):
                compare(expected, actual)
