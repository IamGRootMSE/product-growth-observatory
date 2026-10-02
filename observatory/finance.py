"""Synthetic order economics, exact driver bridges, and leakage-safe forecasts."""
from __future__ import annotations

import argparse
import calendar
from collections import defaultdict
from datetime import date, timedelta
import hashlib
from itertools import permutations
import json
from math import isclose, isfinite
from pathlib import Path
import random
from statistics import mean

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def fixture(seed=20261002):
    """One row/order, one item/order, invented dollars stored as integer cents."""
    rng = random.Random(seed)
    customers, orders = [], []
    for t in range(24):
        year, month = 2024+t//12, 1+t%12
        new = [f'C{len(customers)+i:05}' for i in range(100+t*5)]
        customers += new
        new_set = set(new)
        for customer in customers:
            if customer not in new_set and rng.random() > .22:
                continue
            for _ in range(1 + (rng.random() < .13)):
                premium = rng.random() < (.45 if t < 18 else .30)
                product = 'premium' if premium else 'standard'
                price = (11000 if premium else 5000) - (500 if t >= 18 else 0)
                discount = rng.choice([0, 0, 0, 500])
                cost = (5500 if premium else 2700) + (300 if t >= 18 else 0)
                shipping = 600
                day = rng.randint(1, calendar.monthrange(year, month)[1])
                orders.append(dict(order_id=f'O{len(orders):06}', customer=customer,
                    day=date(year,month,day).isoformat(), product=product,
                    revenue_cents=price-discount, variable_cost_cents=cost+shipping))
    return orders


def model(orders):
    seen = set()
    if not orders:
        raise ValueError('No orders')
    for r in orders:
        if not all(r.get(k) for k in ('order_id','customer','product','day')) or r['order_id'] in seen:
            raise ValueError('Missing key or duplicate order')
        seen.add(r['order_id'])
        date.fromisoformat(r['day'])
        if any(not isinstance(r[k], int) or isinstance(r[k], bool) or r[k] < 0
               for k in ('revenue_cents','variable_cost_cents')):
            raise ValueError('Nonnegative integer cents required')
    con = duckdb.connect()
    con.execute('CREATE TABLE orders(order_id VARCHAR, customer VARCHAR, day DATE, product VARCHAR, revenue_cents BIGINT, variable_cost_cents BIGINT)')
    con.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)',
                    [[r[k] for k in ('order_id','customer','day','product','revenue_cents','variable_cost_cents')] for r in orders])
    con.execute((ROOT/'sql/finance.sql').read_text(encoding='utf-8'))
    return con


def records(con, name):
    cur = con.execute('SELECT * FROM '+name)
    fields = [d[0] for d in cur.description]
    return [dict(zip(fields,row)) for row in cur.fetchall()]


def state(products):
    n = sum(p['orders'] for p in products)
    if n <= 0:
        raise ValueError('Positive period order count required')
    return dict(volume=n, mix={p['product']:p['orders']/n for p in products},
                price={p['product']:p['revenue']/p['orders'] for p in products},
                cost={p['product']:p['cost']/p['orders'] for p in products})


def value(s, margin=True):
    return s['volume'] * sum(s['mix'][p]*(s['price'][p]-(s['cost'][p] if margin else 0)) for p in s['mix'])


def bridge(before, after, margin=True):
    """Shapley allocation: average marginal contribution across every ordering."""
    if set(before['mix']) != set(after['mix']):
        raise ValueError('Bridge requires matched product support; entry/exit needs a separate policy')
    keys = ['volume','mix','price'] + (['cost'] if margin else [])
    effects = dict.fromkeys(keys, 0.)
    paths = list(permutations(keys))
    for path in paths:
        current = dict(before)
        for key in path:
            old = value(current, margin)
            current[key] = after[key]
            effects[key] += (value(current, margin)-old)/len(paths)
    delta = value(after, margin)-value(before, margin)
    if not isclose(sum(effects.values()), delta, abs_tol=1e-7):
        raise AssertionError('Bridge does not reconcile')
    return dict(before=value(before,margin), after=value(after,margin), change=delta,
                effects=effects, residual=delta-sum(effects.values()))


def repeat_cohorts(orders, end_exclusive):
    """First observed order; 90-day maturity applies to entire calendar cohort."""
    people = defaultdict(list)
    for r in orders:
        d = date.fromisoformat(r['day'])
        if d >= end_exclusive:
            raise ValueError('Order at or after observation cutoff')
        people[r['customer']].append(d)
    cohorts = defaultdict(list)
    for days in people.values():
        days.sort()
        cohorts[days[0].strftime('%Y-%m')].append(days)
    result = []
    for cohort, members in sorted(cohorts.items()):
        y,m = map(int,cohort.split('-'))
        month_end = date(y,m,calendar.monthrange(y,m)[1])
        mature = month_end+timedelta(days=90) <= end_exclusive
        k = sum(any(days[0] < d < days[0]+timedelta(days=90) for d in days[1:]) for days in members)
        result.append(dict(cohort=cohort, buyers=len(members), mature=mature,
                           repeat_buyers=k if mature else None,
                           rate=k/len(members) if mature else None))
    return result


def predict(history, method):
    if len(history) < 12:
        raise ValueError('At least 12 complete months required')
    if method == 'seasonal_naive':
        last = history[-12]
        return dict(revenue=last['revenue'], margin=last['margin'])
    if method not in ('last_month','driver_mean3'):
        raise ValueError('Unknown forecast method')
    window = history[-1:] if method == 'last_month' else history[-3:]
    buyers = mean(r['buyers'] for r in window)
    frequency = mean(r['orders']/r['buyers'] for r in window)
    aov = mean(r['revenue']/r['orders'] for r in window)
    margin_per_order = mean(r['margin']/r['orders'] for r in window)
    return dict(revenue=buyers*frequency*aov, margin=buyers*frequency*margin_per_order,
                buyers=buyers, frequency=frequency, aov=aov, margin_per_order=margin_per_order)


def forecast(months):
    if len(months) < 24:
        raise ValueError('24 complete consecutive months required')
    indices = [int(r['month'][:4])*12+int(r['month'][5:7]) for r in months]
    if any(b-a != 1 for a,b in zip(indices,indices[1:])):
        raise ValueError('Missing or unordered months')
    for r in months:
        if any(not isfinite(r[k]) for k in ('buyers','orders','revenue','margin')) or min(r['buyers'],r['orders'],r['revenue']) <= 0:
            raise ValueError('Positive monthly denominators and finite metrics required')
    # Fixed split: months 13-18 select; 19-24 report untouched one-step performance.
    methods = ('last_month','driver_mean3','seasonal_naive')
    def score(method, origins):
        points = []
        for t in origins:
            p = predict(months[:t], method)
            points.append(dict(month=months[t]['month'],actual=months[t]['revenue'],
                predicted=p['revenue'], margin_actual=months[t]['margin'], margin_predicted=p['margin']))
        return dict(wape=sum(abs(p['actual']-p['predicted']) for p in points)/sum(p['actual'] for p in points),
                    margin_mae=mean(abs(p['margin_actual']-p['margin_predicted']) for p in points),points=points)
    selection = {m:score(m,range(12,18)) for m in methods}
    selected = min(methods,key=lambda m:selection[m]['wape'])
    test = {m:score(m,range(18,24)) for m in methods}
    next_month = predict(months,selected)
    drivers = predict(months,'driver_mean3')
    scenarios = []
    for label, demand, price in [('downside',.9,.95),('base',1,1),('upside',1.1,1.05)]:
        orders = drivers['buyers']*drivers['frequency']*demand
        revenue = orders*drivers['aov']*price
        cost_per_order = drivers['aov']-drivers['margin_per_order']
        scenarios.append(dict(name=label,revenue=revenue,margin=revenue-orders*cost_per_order))
    return dict(selected=selected,selection=selection,holdout=test,next_month=next_month,
                scenario_basis='Trailing-three-month driver baseline, not necessarily selected forecast. Demand +/-10%, AOV +/-5%, fixed unit variable cost; not prediction intervals.',
                scenarios=scenarios)


def analyze(orders):
    con = model(orders)
    try:
        months = records(con,'finance_months')
        products = records(con,'finance_products')
        # Independent Python cent reconciliation against SQL aggregates.
        assert isclose(sum(r['revenue'] for r in months),sum(r['revenue_cents'] for r in orders)/100,abs_tol=1e-7)
        assert isclose(sum(r['margin'] for r in months),sum(r['revenue_cents']-r['variable_cost_cents'] for r in orders)/100,abs_tol=1e-7)
        a,b = [state([r for r in products if r['month']==m['month']]) for m in months[-2:]]
        return dict(source='SYNTHETIC independent commerce fixture; no GA4, patient or employer data',
            seed=20261002, orders=len(orders), months=months,
            revenue_bridge=bridge(a,b,False),margin_bridge=bridge(a,b),
            cohorts=repeat_cohorts(orders,date(2026,1,1)), forecast=forecast(months),
            input_sha256=hashlib.sha256(json.dumps(orders,sort_keys=True).encode()).hexdigest(),
            reconciliation='SQL revenue and contribution margin reconciled to Python integer-cent totals')
    finally:
        con.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('outputs/finance'))
    args=parser.parse_args()
    result=analyze(fixture())
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    from .finance_report import render
    (args.output/'index.html').write_text(render(result),encoding='utf-8')
    print(json.dumps(dict(orders=result['orders'],selected=result['forecast']['selected'],
        holdout_wape=result['forecast']['holdout'][result['forecast']['selected']]['wape'],
        margin_change=result['margin_bridge']['change']),indent=2))


if __name__=='__main__':
    main()
