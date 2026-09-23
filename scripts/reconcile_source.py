"""Independent BigQuery source aggregates vs the full CSV export."""
import csv, math, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from observatory.pipeline import load_csv, clean_id

def reconcile(events, audit):
    counts=Counter(r['event_name'] for r in events)
    assert set(counts)=={r['event_name'] for r in audit}, 'Event types differ'
    for a in audit:
        name=a['event_name']; rows=[r for r in events if r['event_name']==name]
        assert counts[name]==int(a['event_count']), f'{name}: row count mismatch'
        assert sum(clean_id(r['user_pseudo_id']) is None for r in rows)==int(a['missing_user_count']), f'{name}: missing users mismatch'
        assert len({clean_id(r['user_pseudo_id']) for r in rows}-{None})==int(a['users']), f'{name}: users mismatch'
        if name=='purchase':
            observed=sum(r['revenue_usd'] or 0 for r in rows)
            expected=float(a['raw_purchase_revenue_usd'] or 0)
            assert math.isclose(observed,expected,abs_tol=.01), 'Purchase revenue mismatch'
    return True

if __name__=='__main__':
    with open(sys.argv[2],newline='',encoding='utf-8-sig') as f: audit=list(csv.DictReader(f))
    reconcile(load_csv(sys.argv[1]),audit)
    print('PASS: full export event counts, missing users, distinct users and purchase USD reconcile with independent source audit.')
