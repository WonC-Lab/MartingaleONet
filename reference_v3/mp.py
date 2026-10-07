"""True MP escalation. Affine variance reuse avoids redundant CF evaluations."""
from dataclasses import replace
import inspect
from reference_v2 import high_precision as original
from reference_v2.high_precision import MPConfig, evaluate, num
from reference_v2.workflow import span,from_row
from reference import route_a as A, route_b as B
from reference.certify import clean

class Integrator(original.Integrator):
    def spectrum(self,v):
        ctx=self.ctx;base=num(ctx,self.case.v);variance=ctx.mpf(v);key=str(variance)
        if key not in self.cache:
            initial=super().spectrum(base)
            self.cache[key]=[(phi*ctx.exp((variance-base)*D),D) for phi,D in initial]
        return self.cache[key]

# Identical physical stencil implementation, with the above independently
# tested affine cache only. This binds a private namespace, not original globals.
_namespace=dict(original.__dict__,Integrator=Integrator)
exec(inspect.getsource(original.finite_differences),_namespace)
finite_differences=_namespace['finite_differences']
FIELDS=['price','Delta','Gamma','Vv']

def worker(r):
    import mpmath
    c=from_row(r);ctx=mpmath.mp.clone();ctx.dps=140
    scales=[1/ctx.mpf(str(c.K)),ctx.mpf(1),ctx.mpf(str(c.K)),1/ctx.mpf(str(c.K))]
    row=dict(input=c.row(),domain=r.get('domain','CORE'),original_flags=r.get('failure_flags',[]),precision=[],degree=[],cutoff=[],A_refinement=[],B_refinement=[])
    required=FIELDS if not r.get('training_required_boundary') else ['price','Delta','Vv'] if c.v==0 else ['price']
    row['required_fields']=required
    try:
        tol=[ctx.mpf(str(r.get('tolerance_'+f,a))) for f,a in zip(FIELDS,[1e-8,2e-6,2e-5,2e-5])]
        def vals(z):return [ctx.mpf(z['values'][f]) for f in FIELDS]
        def diffs(seq):
            ns=[vals(z) for z in seq[-3:]]
            return [max(abs(ns[k+1][j]-ns[k][j]) for k in range(len(ns)-1)) for j in range(4)]
        # The original domain ladder, followed by larger cutoffs only as needed.
        axes=False;fd_ok=False;windows=[]
        cuts=[64,128,256,512,1024,2048,4096,8192,16384,32768]+([65536,131072,262144,524288] if r.get('training_required_boundary') else [])
        for u in cuts:
            row['cutoff'].append(evaluate(c,MPConfig(80,u,40,span(c))))
            if len(row['cutoff'])<3:continue
            delta=diffs(row['cutoff'])
            axes=all(d*s<=t/4 for f,d,s,t in zip(FIELDS,delta,scales,tol) if f in required)
            if not axes:continue
            if required==['price']:
                fd_ok=True;break
            # FD prices need much smaller uncertainty than analytic Greeks.
            # Do not pay for 10 full stencils until propagation can be plausible.
            threshold=ctx.mpf('1e-18') if 'Gamma' in required else ctx.mpf('1e-14')
            if delta[0]*scales[0]>threshold and u<cuts[-1]:continue
            row['MP_FD']=finite_differences(c,MPConfig(80,u,40,span(c)))
            fd=row['MP_FD'];base=[ctx.mpf(fd['base'][f]) for f in FIELDS]
            windows=[]
            for i in range(2,len(fd['rows'])):
                trio=fd['rows'][i-2:i+1];ok=True
                for j,f in enumerate(FIELDS[1:],1):
                    if f not in required:continue
                    numbers=[ctx.mpf(z['values'][f+'5']) for z in trio]
                    error=max(abs(numbers[k+1]-numbers[k]) for k in [0,1])
                    amplification=ctx.mpf(trio[-1]['values'][f+'_amplification'])*delta[0]
                    if max(error,abs(numbers[-1]-base[j]),amplification)*scales[j]>tol[j]/4:ok=False
                if ok:windows.append([z['relative_step'] for z in trio])
            fd_ok=bool(windows)
            if fd_ok:break
        u=row['cutoff'][-1]['config']['cutoff']
        for d in [50,80,120]:row['precision'].append(evaluate(c,MPConfig(d,u,40,span(c))))
        for n in [24,40,64]:row['degree'].append(evaluate(c,MPConfig(80,u,n,span(c))))
        axes=axes and all(max(p,d)*s<=t/4 for f,p,d,s,t in zip(FIELDS,diffs(row['precision']),diffs(row['degree']),scales,tol) if f in required)
        if 'MP_FD' not in row:
            row['MP_FD']=dict(config=MPConfig(80,u,40,span(c)).__dict__,base=row['precision'][-1]['values'],rows=[],warning='Only price is required by this finite Dirichlet trace; no unnecessary FD labels are certified') if required==['price'] else finite_differences(c,MPConfig(80,u,40,span(c)))
        # Revisit quadrature on the measured sufficient integration domain.
        for t in [1e-9,1e-11,1e-13]:
            row['A_refinement'].append(A.price(c,A.Quadrature(cutoff=max(2048,u),atol=t,rtol=t,panels=16)).row())
        row['A']=row['A_refinement'][-1]
        if any(f.startswith('B_') or 'COS' in f for f in row['original_flags']):
            for L in [16,24,32,48]:
                for N in [4096,8192,16384,32768]:row['B_refinement'].append(B.price(c,B.COS(N,L)).row())
            row['B']=row['B_refinement'][-1]
            def bchanges(seq):
                return [max(abs(ctx.mpf(str(seq[k+1][f]))-ctx.mpf(str(seq[k][f]))) for k in range(max(0,len(seq)-3),len(seq)-1)) for f in FIELDS]
            nchange=[ctx.mpf(0)]*4
            for L in [16,24,32,48]:
                seq=[z for z in row['B_refinement'] if z['diagnostics']['config']['L']==L]
                nchange=[max(a,b) for a,b in zip(nchange,bchanges(seq))]
            intervalchange=bchanges([z for z in row['B_refinement'] if z['diagnostics']['config']['N']==32768])
            row['B_convergence_resolved']=all(max(n,l)*s<=t/4 for f,n,l,s,t in zip(FIELDS,nchange,intervalchange,scales,tol) if f in required)
            row['B_last_two_changes']={f:ctx.nstr(max(n,l),50) for f,n,l in zip(FIELDS,nchange,intervalchange)}
        else:row['B']={f:r.get('route_B_'+f) for f in FIELDS}
        candidate=vals(row['precision'][-1]);cross=[max(abs(ctx.mpf(str(row[route][f]))-candidate[j]) for route in ['A','B']) for j,f in enumerate(FIELDS)]
        components={f:('NUMERICALLY_RESOLVED' if axes and cross[j]*scales[j]<=tol[j] and (j==0 or fd_ok) else 'UNRESOLVED') for j,f in enumerate(FIELDS)}
        for f in FIELDS:
            if f not in required:components[f]='UNRESOLVED'
        if row.get('B_convergence_resolved') is False:
            components={f:'UNRESOLVED' for f in FIELDS}
        # Strike identities are also checked by actual MP strike prices.
        obj=Integrator(c,MPConfig(80,u,40,span(c)));K=num(obj.ctx,c.K);S=num(obj.ctx,c.S)
        strike=[]
        for q in (['.0001','.00001','.000001'] if 'strike_FD_derivative_unresolved' in row['original_flags'] and 'Gamma' in required else []):
            h=K*obj.ctx.mpf(q);ps=[]
            for j in [-2,-1,0,1,2]:
                # Construct an exact physical-strike interface via homogeneity;
                # values(S) uses the exact MP S, while K is the exact MP value.
                kk=K+j*h;xx=obj.ctx.log(S/kk)
                disc=obj.ctx.exp(-num(obj.ctx,c.p.r)*num(obj.ctx,c.tau))
                spec=obj.spectrum(num(obj.ctx,c.v))
                integral=obj.ctx.fsum(w*obj.ctx.re(obj.ctx.exp(obj.ctx.j*nu*xx)*phi)/(nu*nu+obj.ctx.mpf('.25')) for w,nu,(phi,D) in zip(obj.weights,obj.u,spec))
                ps.append(S-disc*obj.ctx.sqrt(S*kk)/obj.ctx.pi*integral)
            vk=(ps[0]-8*ps[1]+8*ps[3]-ps[4])/(12*h)
            vkk=(-ps[4]+16*ps[3]-30*ps[2]+16*ps[1]-ps[0])/(12*h*h)
            expected_vk=(candidate[0]-S*candidate[1])/K;expected_vkk=S*S*candidate[2]/(K*K)
            strike.append(dict(relative_step=q,V_K=obj.ctx.nstr(vk,80),V_KK=obj.ctx.nstr(vkk,80),identity_gap=[obj.ctx.nstr(abs(vk-expected_vk),50),obj.ctx.nstr(abs(vkk-expected_vkk),50)]))
        strike_ok=all(ctx.mpf(z['identity_gap'][0])<=tol[0]+S/K*tol[1] and ctx.mpf(z['identity_gap'][1])<=S*S/(K*K*K)*tol[2] for z in strike[-2:])
        if not strike_ok:
            components['Gamma']='UNRESOLVED';components['Delta']='UNRESOLVED'
        # Include all three numerical axes in FD propagation, never just tails.
        uncertainty=max(diffs(row['precision'])[0],diffs(row['degree'])[0],diffs(row['cutoff'])[0])
        propagated=[]
        for window in windows:
            last=next(z for z in row['MP_FD']['rows'] if z['relative_step']==window[-1])
            if all(ctx.mpf(last['values'][f+'_amplification'])*uncertainty*scales[j]<=tol[j]/4 for j,f in enumerate(FIELDS[1:],1) if f in required):propagated.append(window)
        if not propagated and required!=['price']:
            for f in FIELDS[1:]:components[f]='UNRESOLVED'
        if required==['price']:
            for f in FIELDS[1:]:components[f]='UNRESOLVED'
        row.update(component_status=components,status='NUMERICALLY_RESOLVED' if all(components[f]=='NUMERICALLY_RESOLVED' for f in required) else 'UNRESOLVED',valid_FD_windows=propagated,strike_FD_MP=strike,strike_resolved=bool(strike_ok and strike),MP_axes_within_budget=bool(axes),price_diagnostic_uncertainty=ctx.nstr(uncertainty,60),cross_route_max_gap={f:ctx.nstr(z,50) for f,z in zip(FIELDS,cross)})
    except Exception as e:row.update(status='UNRESOLVED',exception=repr(e))
    return clean(row)
