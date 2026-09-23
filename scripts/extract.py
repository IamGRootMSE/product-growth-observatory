"""Optional authenticated extraction. Dry-run only unless --execute is supplied."""
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

def main():
    from google.cloud import bigquery
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True)
    p.add_argument('--maximum-bytes-billed',type=int,default=1_000_000_000)
    p.add_argument('--price-per-tib',type=float,default=None,help='Optional user-verified USD price, not assumed')
    p.add_argument('--execute',action='store_true',help='Explicit authorization to run within the cap; may incur charges')
    a=p.parse_args(); root=Path(__file__).resolve().parents[1]
    client=bigquery.Client(project=a.project)
    sqls=[root/'sql/extract_bigquery.sql',root/'sql/source_audit_bigquery.sql']
    dry=[]
    for path in sqls:
        query=path.read_text(); job=client.query(query,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),location='US')
        estimate=job.total_bytes_processed
        dry.append(dict(file=path.name,sha256=hashlib.sha256(query.encode()).hexdigest(),estimated_bytes=estimate))
        if estimate>a.maximum_bytes_billed: raise SystemExit(f'{path.name}: estimated {estimate} bytes exceeds per-query cap; execution refused')
    total=sum(x['estimated_bytes'] for x in dry)
    print(json.dumps({'dry_runs':dry,'total_estimated_bytes':total,'estimated_usd_before_free_allowance':None if a.price_per_tib is None else total/2**40*a.price_per_tib},indent=2))
    if not a.execute: return
    out=root/'data/raw'; out.mkdir(parents=True,exist_ok=True)
    for path,meta,name in zip(sqls,dry,['events.csv','source-audit.csv']):
        job=client.query(path.read_text(),location='US',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=a.maximum_bytes_billed))
        result=job.result()
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f); writer.writerow([s.name for s in result.schema]); writer.writerows(list(row.values()) for row in result)
        meta.update(job_id=job.job_id,total_bytes_processed=job.total_bytes_processed,total_bytes_billed=job.total_bytes_billed)
    (out/'manifest.json').write_text(json.dumps(dict(extracted_at=datetime.now(timezone.utc).isoformat(),project=a.project,queries=dry),indent=2))
    print('Saved ignored data/raw/events.csv, source-audit.csv and manifest.json. Check schema and reconcile before publication.')
if __name__=='__main__': main()
