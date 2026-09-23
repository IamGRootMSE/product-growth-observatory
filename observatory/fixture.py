"""Deterministic fabricated journeys. Never evidence about Google customers."""
from datetime import datetime, timedelta, timezone
import random

FIELDS = ['event_date','event_timestamp','event_name','user_pseudo_id','ga_session_id',
          'session_param_count','device','acquisition_source','acquisition_medium',
          'transaction_id','revenue_usd','revenue_local','currency','event_value']

def generate(n=1200, seed=20260923):
    rng = random.Random(seed)
    start = datetime(2020, 11, 1, tzinfo=timezone.utc)
    end = datetime(2021, 2, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        user = f'fixture-{i:05d}'
        device = rng.choices(['desktop','mobile','tablet',None],[45,48,5,2])[0]
        source, medium = rng.choice([('google','organic'),('google','cpc'),('(direct)','(none)'),('newsletter','email'),(None,None)])
        first = start + timedelta(days=rng.randrange(92), hours=rng.randrange(22))
        visits = [0] + ([rng.randrange(1,8)] if rng.random()<.36 else []) + ([rng.randrange(8,29)] if rng.random()<.20 else [])
        for v, day in enumerate(sorted(set(visits))):
            ts = first + timedelta(days=day)
            if ts >= end: continue
            sid = int(ts.timestamp())
            names = ['session_start','page_view','view_item']
            if rng.random() < (.58 if device=='desktop' else .40):
                names += ['add_to_cart']
                if rng.random() < .64:
                    names += ['begin_checkout']
                    if rng.random() < .64: names += ['purchase']
            # Cross-session completions demonstrate different funnel scope.
            if v and rng.random()<.18: names = ['session_start','begin_checkout','purchase']
            for j, name in enumerate(names):
                stamp = ts + timedelta(seconds=j*45)
                order = f'order-{i}-{v}' if name=='purchase' else None
                revenue = float(rng.randrange(20,160)) if order else None
                r = dict(zip(FIELDS,[stamp.strftime('%Y%m%d'),int(stamp.timestamp()*1e6),name,user,sid,1,device,source,medium,order,revenue,revenue,'USD' if order else None,revenue]))
                rows.append(r)
                if order and rng.random()<.09: rows.append(dict(r))
    # Explicit quality edge cases, with valid schema.
    for kind in ['missing_user','missing_session','missing_transaction','duplicate_param']:
        r = dict(rows[0]); r.update(event_name='purchase',transaction_id=None,revenue_usd=25.0)
        if kind=='missing_user': r['user_pseudo_id']=None
        if kind=='missing_session': r['ga_session_id']=None
        if kind=='duplicate_param': r['session_param_count']=2
        rows.append(r)
    return sorted(rows,key=lambda r:r['event_timestamp'])
