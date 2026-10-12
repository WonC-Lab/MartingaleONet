"""Streaming arbitrary precision Lewis and independent hyperbolic COS.

No CUDA/NumPy pricing and no float64 numbers in the pricing algebra. COS
interval selection uses the original, deliberately heuristic cumulants; the
interval is fixed at base maturity/variance during all derivative stencils.
"""
from types import SimpleNamespace
from reference_v2.high_precision import context, cf, gaussian_rule
from reference import route_b
from reference.types import Parameters, Case

FIELDS = ('c', 'Delta', 'nu')


def parameters(row):
    return SimpleNamespace(**{k: str(row[k]) for k in ('kappa','theta','sigma','rho','r')})


def hyperbolic_cf(ctx, u, v, tau, p):
    u=ctx.mpc(u); v=ctx.mpf(v); t=ctx.mpf(tau)
    k,theta,sigma,rho,r=[ctx.mpf(getattr(p,f)) for f in ('kappa','theta','sigma','rho','r')]
    if u==0: return ctx.mpc(1),ctx.mpc(0)
    if u==-ctx.j: return ctx.exp(r*t),ctx.mpc(0)
    if sigma==0:
        av=t if k==0 else -ctx.expm1(-k*t)/k
        iv=v*t if k==0 else theta*t+(v-theta)*av
        D=-(u*u+ctx.j*u)*av/2
        return ctx.exp(ctx.j*u*r*t-(u*u+ctx.j*u)*iv/2),D
    beta=k-ctx.j*rho*sigma*u
    d=ctx.sqrt(beta**2+sigma**2*(u*u+ctx.j*u))
    if ctx.re(d)<0: d=-d
    decay=ctx.exp(-d*t); th=-ctx.expm1(-d*t)/(1+decay)
    D=-(u*u+ctx.j*u)*th/(d+beta*th)
    logH=d*t/2+ctx.log(((1+beta/d)+(1-beta/d)*decay)/2)
    C=k*theta/sigma**2*(beta*t-2*logH)
    return ctx.exp(ctx.j*u*r*t+C+v*D),D


def cos_interval(row,L):
    p=Parameters(**{k:float(row[k]) for k in ('kappa','theta','sigma','rho','r')})
    case=Case(x=float(row['x']),v=0,tau=float(row['tau']),K=1,p=p)
    a,b=route_b.interval(case,L)
    return str(a),str(b)


def evaluate(row, route, cfg, coordinates, tick=lambda:None, saved=None, checkpoint=lambda z:None):
    """Evaluate same-time coordinates together, sharing CF and affine v reuse.

    coordinates are exact decimal (x,v,tau) triples. Sum signed and absolute
    summands incrementally, retaining bounded memory rather than full grids.
    """
    ctx=context(cfg['dps']); p=parameters(row)
    pts=[tuple(ctx.mpf(str(z)) for z in q) for q in coordinates]
    sums=[[ctx.mpf(0) for _ in range(3)] for _ in pts]
    absolute=[[ctx.mpf(0) for _ in range(3)] for _ in pts]
    groups={}
    for i,(_,_,t) in enumerate(pts): groups.setdefault(str(t),[]).append(i)
    nodes=0; resume_nodes=0
    if saved:
        resume_nodes=saved['nodes']
        sums=[[ctx.make_mpf(tuple(z)) for z in q] for q in saved['sums']]
        absolute=[[ctx.make_mpf(tuple(z)) for z in q] for q in saved['absolute']]
    def persist():
        checkpoint({'nodes':nodes,'sums':[[list(map(int,z._mpf_)) for z in q] for q in sums],
                    'absolute':[[list(map(int,z._mpf_)) for z in q] for q in absolute]})
    if route=='E1':
        degree=cfg['degree']; base,weights=gaussian_rule(cfg['dps'],degree)
        maximum=ctx.pi*degree/(4*max(ctx.mpf(str(cfg['span'])),ctx.mpf('.01')))
        def grid():
            left=ctx.mpf(0); width=ctx.mpf(1); cutoff=ctx.mpf(cfg['cutoff'])
            while left<cutoff:
                right=min(cutoff,left+min(width,maximum)); mid=(left+right)/2; half=(right-left)/2
                for z,w in zip(base,weights): yield mid+half*z,half*w
                left=right; width*=2
        iterator=grid()
    elif route=='E2':
        a,b=map(ctx.mpf,cos_interval(row,cfg['L'])); length=b-a
        lo=a; hi=min(b,ctx.mpf(0))
        def grid():
            for n in range(cfg['N']):
                u=n*ctx.pi/length
                if hi<=lo: coeff=ctx.mpf(0)
                else:
                    arglo=u*(lo-a); arghi=u*(hi-a)
                    chi=(ctx.exp(hi)*(ctx.cos(arghi)+u*ctx.sin(arghi))-ctx.exp(lo)*(ctx.cos(arglo)+u*ctx.sin(arglo)))/(1+u*u)
                    psi=hi-lo if n==0 else (ctx.sin(arghi)-ctx.sin(arglo))/u
                    coeff=2/length*(psi-chi)
                    if n==0: coeff/=2
                yield u,coeff
        iterator=grid()
    else: raise ValueError(route)
    for u,w in iterator:
        if nodes<resume_nodes:
            nodes+=1;continue
        if nodes%128==0:
            try: tick()
            except Exception:
                persist();raise
        if nodes%4096==0: persist()
        nodes+=1
        for t,indices in groups.items():
            phi,D=(cf(ctx,u-ctx.j/2,0,t,p,True) if route=='E1' else hyperbolic_cf(ctx,u,0,t,p))
            for i in indices:
                x,v,_=pts[i]; z=phi*ctx.exp(v*D)*ctx.exp(ctx.j*u*(x if route=='E1' else x-a))
                if route=='E1':
                    vals=[w*ctx.re(z)/(u*u+ctx.mpf('.25')),
                          w*ctx.re((ctx.mpf('.5')+ctx.j*u)*z)/(u*u+ctx.mpf('.25')),
                          w*ctx.re(z*D)/(u*u+ctx.mpf('.25'))]
                else: vals=[w*ctx.re(z),w*ctx.re(ctx.j*u*z),w*ctx.re(D*z)]
                for j,zv in enumerate(vals): sums[i][j]+=zv; absolute[i][j]+=abs(zv)
    persist()
    eps=ctx.power(2,1-ctx.prec); m=64*nodes+256
    if m*eps>=1: raise ArithmeticError('invalid roundoff allowance')
    gamma=m*eps/(1-m*eps); out=[]
    for (x,v,t),s,ab in zip(pts,sums,absolute):
        S=ctx.exp(x); disc=ctx.exp(-ctx.mpf(p.r)*t)
        if route=='E1':
            scale=disc*ctx.sqrt(S)/ctx.pi
            values=[S-scale*s[0],1-scale/S*s[1],-scale*s[2]]
            allowances=[gamma*(S+scale*ab[0]),gamma*(1+scale/S*ab[1]),gamma*scale*ab[2]]
        else:
            values=[disc*s[0]+S-disc,1+disc*s[1]/S,disc*s[2]]
            allowances=[gamma*(disc*ab[0]+S+disc),gamma*(1+disc*ab[1]/S),gamma*disc*ab[2]]
        if not all(ctx.isfinite(z) for z in values+allowances): raise ArithmeticError('nonfinite result')
        out.append({'values':{k:ctx.nstr(z,ctx.dps) for k,z in zip(FIELDS,values)},
                    'roundoff':{k:ctx.nstr(z,ctx.dps) for k,z in zip(FIELDS,allowances)}})
    return {'route':route,'config':cfg,'nodes':nodes,'actual_bit_precision':ctx.prec,
            'coordinates':[list(map(str,q)) for q in coordinates], 'results':out,
            'COS_interval':cos_interval(row,cfg['L']) if route=='E2' else None,
            'raw_unclipped':True,'roundoff_is_interval_enclosure':False}
