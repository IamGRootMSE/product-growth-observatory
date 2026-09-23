"""Standard-library statistics with explicit assumptions."""
from math import sqrt, ceil
from statistics import NormalDist
import random

def wilson(k,n):
    if not n: return [None,None]
    z=NormalDist().inv_cdf(.975); p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def difference(k1,n1,k0,n0):
    if not n1 or not n0: return {'estimate':None,'ci':[None,None]}
    p1,p0=k1/n1,k0/n0; a,b=wilson(k1,n1); c,d=wilson(k0,n0)
    delta=p1-p0
    return {'estimate':delta,'ci':[max(-1,delta-sqrt((p1-a)**2+(d-p0)**2)),min(1,delta+sqrt((b-p1)**2+(p0-c)**2))]}

def cluster_interval(records, reps=500):
    """Percentile bootstrap over user clusters of session success/denominator."""
    clusters={}
    for r in records:
        if r['stage']:
            a=clusters.setdefault(r['user'],[0,0]); a[0]+=r['stage']==4; a[1]+=1
    values=list(clusters.values())
    if not values: return [None,None]
    rng=random.Random(197); rates=[]
    for _ in range(reps):
        sample=rng.choices(values,k=len(values)); rates.append(sum(a for a,b in sample)/sum(b for a,b in sample))
    rates.sort()
    return [rates[int(.025*reps)],rates[min(reps-1,int(.975*reps))]]

def sample_size(baseline=.15, absolute_mde=.03, alpha=.05, power=.8, daily_users=500):
    if not (0<baseline<1 and 0<absolute_mde<1-baseline and 0<alpha<1 and .5<power<1 and daily_users>0):
        raise ValueError('Invalid experiment assumptions')
    p0=baseline; p1=p0+absolute_mde; pooled=(p0+p1)/2
    z=NormalDist().inv_cdf(1-alpha/2); zb=NormalDist().inv_cdf(power)
    n=ceil((z*sqrt(2*pooled*(1-pooled))+zb*sqrt(p0*(1-p0)+p1*(1-p1)))**2/absolute_mde**2)
    enrollment=max(14,ceil((2*n/daily_users)/7)*7)
    return dict(per_arm=n,total=2*n,enrollment_days=enrollment,readout_days=enrollment+7,baseline=p0,absolute_mde=absolute_mde,alpha=alpha,power=power,daily_users=daily_users)
