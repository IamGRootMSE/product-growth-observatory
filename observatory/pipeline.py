"""Reproducible GA4 analysis: python -m observatory.pipeline --fixture."""
import argparse, csv, hashlib, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import duckdb
from .fixture import generate, FIELDS
from .stats import wilson, difference, cluster_interval, sample_size

ROOT=Path(__file__).resolve().parents[1]
STEPS=['view_item','add_to_cart','begin_checkout','purchase']
DAY=86400*1000000

def clean_id(value):
    return value if value not in (None,'','<Other>','(not set)') else None

def model(rows):
    con=duckdb.connect()
    types=['VARCHAR','BIGINT','VARCHAR','VARCHAR','BIGINT','INTEGER','VARCHAR','VARCHAR','VARCHAR','VARCHAR','DOUBLE','DOUBLE','VARCHAR','DOUBLE']
    con.execute('CREATE TABLE raw ('+','.join(f'{k} {t}' for k,t in zip(FIELDS,types))+')')
    con.executemany('INSERT INTO raw VALUES ('+','.join('?' for _ in FIELDS)+')',[[r.get(k) for k in FIELDS] for r in rows])
    con.execute((ROOT/'sql/models.sql').read_text())
    return con

def records(con,table):
    cur=con.execute('SELECT * FROM '+table)
    names=[d[0] for d in cur.description]
    return [dict(zip(names,r)) for r in cur.fetchall()]

def ordered_stage(events, window=None):
    """Strict timestamp ordering; ties do not establish temporal order."""
    anchor=None; last=None; stage=0
    for e in sorted(events,key=lambda e:(e['event_timestamp'],e['event_id'])):
        ts=e['event_timestamp']
        if stage==0 and e['event_name']==STEPS[0]: anchor=last=ts; stage=1
        elif stage and stage<4 and e['event_name']==STEPS[stage] and ts>last and (window is None or ts<anchor+window):
            last=ts; stage+=1
    return stage,anchor

def funnel_records(events, purchases, end):
    canonical={r['event_id'] for r in purchases}
    by_session=defaultdict(list); by_user=defaultdict(list)
    for e in events:
        if e['session_key']: by_session[e['session_key']].append(e)
        if e['user_key']: by_user[e['user_key']].append(e)
    sessions=[]; users=[]; immature=0
    for key,es in by_session.items():
        first=min(es,key=lambda e:(e['event_timestamp'],e['event_id']))
        stage,_=ordered_stage([e for e in es if e['event_name']!='purchase' or e['event_id'] in canonical])
        sessions.append(dict(key=key,user=first['user_key'],device=first['device_group'],channel=first['channel'],stage=stage))
    for key,es in by_user.items():
        stage,anchor=ordered_stage([e for e in es if e['event_name']!='purchase' or e['event_id'] in canonical],7*DAY)
        if not stage: continue
        if anchor+7*DAY>end: immature+=1; continue
        first=min((e for e in es if e['event_name']=='view_item'),key=lambda e:(e['event_timestamp'],e['event_id']))
        users.append(dict(key=key,user=key,device=first['device_group'],channel=first['channel'],stage=stage))
    return sessions,users,immature

def summarize(rs,mode):
    counts=[sum(r['stage']>=i for r in rs) for i in range(1,5)]
    n=counts[0]; k=counts[3]
    return dict(counts=counts,n=n,k=k,rate=k/n if n else None,ci=cluster_interval(rs) if mode=='session' else wilson(k,n),small=n<30)

def retention(events,purchases,end):
    es=defaultdict(list); ps=defaultdict(list)
    for e in events:
        if e['user_key']: es[e['user_key']].append(e)
    for p in purchases:
        if p['user_key']: ps[p['user_key']].append(p['event_timestamp'])
    groups=defaultdict(list)
    for u,rows in es.items():
        first=min(r['event_timestamp'] for r in rows)
        dt=datetime.fromtimestamp(first/1e6,timezone.utc)
        week=(dt-timedelta(days=dt.weekday())).date().isoformat()
        groups[week].append((u,first,rows))
    cells=[]
    for week,people in sorted(groups.items()):
        for w in range(1,5):
            # Require entire observed cohort to mature; never shrink denominator to its early entrants.
            eligible=max(first for _,first,_ in people)+(7*w+1)*DAY<=end
            k=0
            for u,first,rows in people:
                # New session starting on elapsed days [1,8), [8,15), etc.
                starts={}
                for r in rows:
                    if r['session_key']: starts[r['session_key']]=min(starts.get(r['session_key'],r['event_timestamp']),r['event_timestamp'])
                k+=any(first+(1+7*(w-1))*DAY<=t<first+(1+7*w)*DAY for t in starts.values())
            n=len(people)
            cells.append(dict(cohort=week,week=w,n=n,k=k if eligible else None,rate=k/n if eligible else None,ci=wilson(k,n) if eligible else [None,None],eligible=eligible))
    # Repeat purchase: first observed purchase anchors 28-day follow-up, distinct order strictly later.
    eligible_buyers=[sorted(times) for times in ps.values() if min(times)+28*DAY<=end]
    repeat=sum(any(t[0]<x<t[0]+28*DAY for x in t[1:]) for t in eligible_buyers)
    return cells,dict(n=len(eligible_buyers),k=repeat,rate=repeat/len(eligible_buyers) if eligible_buyers else None,ci=wilson(repeat,len(eligible_buyers)))

def analyze(rows, source, start='2020-11-01', end='2021-02-01'):
    end_us=int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp()*1e6)
    start_us=int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp()*1e6)
    # UTC window explicitly separates extraction property dates from analysis timestamps.
    bounded=[r for r in rows if start_us<=int(r['event_timestamp'])<end_us]
    if not bounded: raise ValueError('No events in declared observation window')
    con=model(bounded); events=records(con,'events'); purchases=records(con,'purchases')
    sr,ur,immature=funnel_records(events,purchases,end_us)
    devices=sorted({e['device_group'] for e in events}); channels=sorted({e['channel'] for e in events})
    funnels=[]
    for mode,rs in [('session',sr),('user',ur)]:
        for device in ['All']+devices:
            for channel in ['All']+channels:
                selected=[r for r in rs if (device=='All' or r['device']==device) and (channel=='All' or r['channel']==channel)]
                funnels.append(dict(mode=mode,device=device,channel=channel,**summarize(selected,mode)))
    cohorts,repeat=retention(events,purchases,end_us)
    raw_counts=Counter(r['event_name'] for r in bounded)
    model_counts=Counter(r['event_name'] for r in events)
    raw_purchase=[e for e in events if e['event_name']=='purchase']
    known=[e for e in raw_purchase if e['transaction_key']]
    conflicts=con.execute("SELECT count(*) FROM (SELECT transaction_key FROM events WHERE event_name='purchase' AND transaction_key IS NOT NULL GROUP BY 1 HAVING count(DISTINCT revenue_usd)>1 OR count(DISTINCT user_key)>1)").fetchone()[0]
    quality=dict(raw_rows=len(rows),in_window_rows=len(bounded),outside_utc_window=len(rows)-len(bounded),modeled_events=len(events),
        missing_user=sum(e['user_key'] is None for e in events),missing_session=sum(e['session_key'] is None for e in events),
        repeated_session_parameter=sum(e['session_param_count']>1 for e in events),
        raw_purchases=len(raw_purchase),missing_transaction=len(raw_purchase)-len(known),duplicate_purchases=len(known)-len(purchases),
        canonical_purchases=len(purchases),conflicting_transactions=conflicts,
        raw_revenue_usd=sum(e['revenue_usd'] or 0 for e in raw_purchase),canonical_revenue_usd=sum(e['revenue_usd'] or 0 for e in purchases),
        unknown_canonical_revenue=sum(e['revenue_usd'] is None for e in purchases),immature_user_funnels=immature,
        sessions=len(sr),users=con.execute('SELECT count(*) FROM users').fetchone()[0],
        source_counts=dict(sorted(raw_counts.items())),model_counts=dict(sorted(model_counts.items())),reconciled=raw_counts==model_counts)
    assert quality['reconciled']
    assert quality['raw_purchases']==quality['canonical_purchases']+quality['duplicate_purchases']+quality['missing_transaction']
    comparisons=[]
    for dim,values in [('device',devices),('channel',channels)]:
        for value in values:
            a=[r for r in ur if r[dim]==value]; b=[r for r in ur if r[dim]!=value]
            k=sum(r['stage']==4 for r in a); kb=sum(r['stage']==4 for r in b)
            comparisons.append(dict(dimension=dim,segment=value,n=len(a),k=k,rate=k/len(a) if a else None,ci=wilson(k,len(a)),reference_n=len(b),reference_k=kb,small=min(len(a),len(b))<30,difference=difference(k,len(a),kb,len(b))))
    all_session=next(f for f in funnels if f['mode']=='session' and f['device']=='All' and f['channel']=='All')
    counts=all_session['counts']; losses=[counts[i]-counts[i+1] for i in range(3)]; bottleneck=losses.index(max(losses))
    # Evidence anchors are computed; hypotheses remain conditional until real extraction.
    weakest=min((c for c in comparisons if c['dimension']=='device' and not c['small']),key=lambda c:c['rate'],default=None)
    hypotheses=[dict(priority=1,title='Investigate the largest journey loss',evidence=f"{losses[bottleneck]:,} of {counts[bottleneck]:,} entrants do not reach {STEPS[bottleneck+1]} in order within the same session.",action=f"Audit {STEPS[bottleneck]} → {STEPS[bottleneck+1]} event coverage, then review the interface for cost or action clarity.",falsifier='The gap disappears after instrumentation repair or reflects low-intent browsing.'),
      dict(priority=2,title='Check device-specific friction',evidence=(f"{weakest['segment']}: {weakest['k']}/{weakest['n']} mature viewers purchase within the ordered seven-day funnel." if weakest else 'No device has enough mature viewers to prioritize.'),action='Stratify by acquisition and inspect page performance and cart usability before proposing a device-targeted test.',falsifier='Within-channel gaps vanish, or page diagnostics show no device-specific friction.'),
      dict(priority=3,title='Investigate reasons to return',evidence=f"{repeat['k']}/{repeat['n']} eligible first-observed buyers place another distinct order within 28 days.",action='Interview returning and one-time buyers; test whether useful post-purchase guidance merits a later experiment.',falsifier='Purchase cadence exceeds this observation window or obfuscation breaks identity continuity.')]
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    return dict(title='Product Funnel & Retention Observatory',source=source,window=dict(start=start,end_exclusive=end,timezone='UTC'),input_sha256=digest,
        devices=devices,channels=channels,funnels=funnels,cohorts=cohorts,repeat_purchase=repeat,quality=quality,comparisons=comparisons,hypotheses=hypotheses,experiment=sample_size(),
        provenance=dict(dataset='bigquery-public-data.ga4_obfuscated_sample_ecommerce',verified_on='2026-09-23',source_url='https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset',cloud_query_executed=False if source=='synthetic fixture' else None,source_reconciliation='local input aggregates; independent BigQuery reconciliation pending' if source!='synthetic fixture' else 'generated fixture vs modeled aggregates'))

def load_csv(path):
    rows=[]
    with open(path,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not set(FIELDS)<=set(reader.fieldnames or []): raise ValueError('CSV must match sql/extract_bigquery.sql columns')
        for row in reader:
            r={k:(row[k] if row[k] not in ('','NULL') else None) for k in FIELDS}
            for k in ['event_timestamp','ga_session_id','session_param_count']: r[k]=int(r[k]) if r[k] is not None else None
            for k in ['revenue_usd','revenue_local','event_value']: r[k]=float(r[k]) if r[k] is not None else None
            if r['event_timestamp'] is None: raise ValueError('Missing event timestamp')
            rows.append(r)
    return rows

def main():
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True); g.add_argument('--fixture',action='store_true'); g.add_argument('--input',type=Path)
    p.add_argument('--start',default='2020-11-01'); p.add_argument('--end-exclusive',default='2021-02-01'); p.add_argument('--output',type=Path,default=ROOT/'site/data.json')
    args=p.parse_args(); rows=generate() if args.fixture else load_csv(args.input)
    result=analyze(rows,'synthetic fixture' if args.fixture else 'GA4 exported sample (user supplied)',args.start,args.end_exclusive)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(output=str(args.output),source=result['source'],quality=result['quality']),indent=2))

if __name__=='__main__': main()
