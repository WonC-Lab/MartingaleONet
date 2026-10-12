"""Frozen v6.0 decision mathematics. Contains no pricing or execution runner."""
from decimal import Decimal, getcontext
import hashlib
import json
import subprocess
from pathlib import Path

VERSION='limiting-v0-certification-v6.0'
getcontext().prec=160
D=lambda v:Decimal(str(v))

def verify_freeze(root):
    root=Path(root)
    receipt=json.loads((root/'PROTOCOL_FREEZE_RECEIPT.json').read_text(encoding='utf-8'))
    for name,expected in receipt['frozen_file_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Frozen artifact mismatch: '+name)
        blob=subprocess.check_output(['git','show',receipt['git_commit']+':reference_v6/'+name],cwd=root.parent)
        if hashlib.sha256(blob).hexdigest()!=expected:raise RuntimeError('Frozen Git artifact mismatch: '+name)
    for name,expected in receipt['code_version']['reference_canonical_lf_sha256'].items():
        data=(root.parent/name).read_bytes().replace(b'\r\n',b'\n')
        if hashlib.sha256(data).hexdigest()!=expected:raise RuntimeError('Reference source changed: '+name)
    return receipt

def normalized_residual(c,delta,nu,ctau,row):
    """Signed tau_star R0 / C_star, with tau_star=C_star=1."""
    x=D(row['x']);r=D(row['r']);kt=D(row['kappa'])*D(row['theta'])
    return D(ctau)-r*x.exp()*D(delta)-kt*D(nu)+r*D(c)

def component_budgets(values1,values2,row):
    c=max(abs(D(z['c'])) for z in [values1,values2])
    delta=max(abs(D(z['Delta'])) for z in [values1,values2])
    nu=max(abs(D(z['nu'])) for z in [values1,values2])
    tc=D('1e-8')+D('1e-6')*c
    td=D('2e-6')+D('1e-5')*delta
    tn=D('2e-5')+D('1e-4')*nu
    r=abs(D(row['r']));kt=abs(D(row['kappa'])*D(row['theta']))
    br=tc+r*D(row['x']).exp()*td+kt*tn+r*tc
    return dict(T_C=tc,T_Delta=td,T_nu=tn,T_ctau=tc,B_R=br)

def time_fd5(prices,h):
    a=list(map(D,prices));h=D(h)
    return (a[0]-8*a[1]+8*a[3]-a[4])/(12*h)

def propagated_time_uncertainty(price_uncertainties,h):
    a=[1,8,0,8,1]
    return sum(D(z)*w for z,w in zip(price_uncertainties,a))/(12*D(h))

def truncation_policy(d_j,d_prev):
    dj=abs(D(d_j));dp=abs(D(d_prev))
    return dict(richardson_finest=dj/15,richardson_previous_scaled=dp/240,
                conservative_guard=max(dj,dp))

def residual_uncertainty(u_tau,u_delta,u_nu,u_c,row):
    r=abs(D(row['r']));kt=abs(D(row['kappa'])*D(row['theta']))
    return D(u_tau)+r*D(row['x']).exp()*D(u_delta)+kt*D(u_nu)+r*D(u_c)

def level_accepts(rhat,uhat,br):
    """Alpha=1: zero consistency AND precision cap; not a statistical CI."""
    return abs(D(rhat))<=D(uhat) and D(uhat)<=D(br)/4

def estimator_window_accepts(levels,br):
    """All three levels are checked; caller must also verify reference axes."""
    if len(levels)!=3:return False
    br=D(br)
    if not all(level_accepts(z['R_hat'],z['u_R_hat'],br) for z in levels):return False
    u=[D(z['u_R_hat']) for z in levels]
    if u[1]>2*u[0] or u[2]>2*u[1]:return False
    d=[abs(D(levels[i+1]['D5'])-D(levels[i]['D5'])) for i in [0,1]]
    if max(d)>br/4:return False
    # Either at least one-bit contraction, or measured differences are below
    # the independently propagated time-price uncertainty at both comparisons.
    contraction=d[1]<=d[0]/2
    noise=all(d[i]<=D(levels[i]['u_tau_price'])+D(levels[i+1]['u_tau_price']) for i in [0,1])
    return contraction or noise
