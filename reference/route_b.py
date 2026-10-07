"""Independent Riccati hyperbolic solution and analytic COS put coefficients.

No imports from Route A. Local derivatives hold [a,b] fixed. Cumulants are
obtained by solving the degree-four log-CF Taylor Riccati equations, rather
than differentiating the Route A algebra.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import math
import numpy as np
from scipy.integrate import solve_ivp
from .types import Estimate

@dataclass(frozen=True)
class COS:
    N: int = 2048
    L: float = 16.
    interval: tuple | None = None

def cf(u,v,tau,p,return_D=False):
    u=np.asarray(u,dtype=complex)
    if p.sigma == 0:
        A=tau if p.kappa==0 else -np.expm1(-p.kappa*tau)/p.kappa
        I=v*tau if p.kappa==0 else p.theta*tau+(v-p.theta)*A
        D=-(u*u+1j*u)*A/2
        value=np.exp(1j*u*p.r*tau-(u*u+1j*u)*I/2)
    else:
        original=u
        u=np.where((u==0)|(u==-1j),1.+0j,u)
        beta=p.kappa-1j*p.rho*p.sigma*u
        disc=np.sqrt(beta**2+p.sigma**2*(u*u+1j*u))
        disc=np.where(disc.real<0,-disc,disc)
        half=disc*tau/2
        # Real(disc)>=0: exponential form avoids NumPy tanh overflow warnings.
        decay=np.exp(-2*half)
        th=-np.expm1(-2*half)/(1+decay)
        D=-(u*u+1j*u)*th/(disc+beta*th)
        # scaled hyperbolic denominator: avoids cosh overflow at high u.
        logH=half+np.log(((1+beta/disc)+(1-beta/disc)*decay)/2)
        C=p.kappa*p.theta/p.sigma**2*(beta*tau-2*logH)
        value=np.exp(1j*u*p.r*tau+C+v*D)
        value=np.where(original==0,1.+0j,value)
        value=np.where(original==-1j,np.exp(p.r*tau)+0j,value)
        D=np.where((original==0)|(original==-1j),0.+0j,D)
    return (value,D) if return_D else value

@lru_cache(maxsize=16384)
def cumulants(v,tau,p):
    def ode(t,y):
        d=y[:5]; dd=-p.kappa*d+.5*p.sigma**2*np.convolve(d,d)[:5]
        dd[1:]+=1j*p.rho*p.sigma*d[:-1]
        dd[1]-=.5j; dd[2]-=.5
        return np.r_[dd,p.kappa*p.theta*d]
    sol=solve_ivp(ode,(0,tau),np.zeros(10,complex),rtol=2e-11,atol=2e-13,method="DOP853")
    if not sol.success: raise ArithmeticError(sol.message)
    coeff=sol.y[5:,-1]+v*sol.y[:5,-1]; coeff[1]+=1j*p.r*tau
    ks=[float(np.real(coeff[n]*math.factorial(n)/(1j**n))) for n in (1,2,4)]
    if ks[1] <= 0 or not np.all(np.isfinite(ks)): raise ArithmeticError(f"invalid cumulants: {ks}")
    return tuple(ks)

def interval(case,L):
    c1,c2,c4=cumulants(case.v,case.tau,case.p)
    width=L*np.sqrt(c2+np.sqrt(abs(c4)))
    return (case.x+c1-width,case.x+c1+width)

def coefficients(u,a,b,kind):
    lo=max(a,0.) if kind=="call" else a
    hi=b if kind=="call" else min(b,0.)
    if hi <= lo: return np.zeros_like(u)
    arglo=u*(lo-a); arghi=u*(hi-a)
    chi=(np.exp(hi)*(np.cos(arghi)+u*np.sin(arghi))-
         np.exp(lo)*(np.cos(arglo)+u*np.sin(arglo)))/(1+u*u)
    psi=np.empty_like(u); psi[0]=hi-lo
    psi[1:]=(np.sin(arghi[1:])-np.sin(arglo[1:]))/u[1:]
    return chi-psi if kind=="call" else psi-chi

def price(case,config=COS()):
    if case.tau <= 0: raise ValueError("COS requires positive maturity; terminal payoff bypass handled by caller")
    if case.v<0: raise ValueError("negative variance")
    a,b=config.interval or interval(case,config.L)
    if not a<b or config.N<2: raise ValueError("invalid COS configuration")
    u=np.arange(config.N)*np.pi/(b-a)
    phi,D=cf(u,case.v,case.tau,case.p,True)
    phase=phi*np.exp(1j*u*(case.x-a))
    weights=2/(b-a)*coefficients(u,a,b,"put"); weights[0]*=.5
    disc=np.exp(-case.p.r*case.tau)
    def summation(z): return math.fsum((weights*np.real(z)).tolist())*disc
    put=summation(phase); px=summation(1j*u*phase); pxx=summation(-u*u*phase)
    cv=summation(D*phase)
    c=put+np.exp(case.x)-disc
    delta=1+px/np.exp(case.x); gamma=(pxx-px)/(case.K*np.exp(2*case.x))
    cw=2/(b-a)*coefficients(u,a,b,"call"); cw[0]*=.5
    direct=disc*math.fsum((cw*phase.real).tolist())
    nu=case.K*cv
    return Estimate(float(case.K*c),float(delta),float(gamma),float(nu),float(2*np.sqrt(case.v)*nu),
        {"route":"B","config":asdict(config),"interval":[float(a),float(b)],
         "cumulants":list(cumulants(case.v,case.tau,case.p)),"put":float(case.K*put),
         "direct_call":float(case.K*direct),"parity_direct_gap":float(case.K*abs(c-direct)),
         "fixed_interval_derivatives":True,"raw_unclipped":True,"tail_error_certified":False})
