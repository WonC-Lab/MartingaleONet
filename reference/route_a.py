"""Little-trap CF and P1/P2 inversion; independent of COS implementation.

psi is the CF of log(ST/S), with q=0. No strike in this CF.
Zero-frequency limits follow expected integrated variance under money/stock
numeraire measures. No epsilon denominator and no output clipping.
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.integrate import quad_vec
from scipy.special import ndtr
from .types import Estimate

@dataclass(frozen=True)
class Quadrature:
    cutoff: float = 512.
    atol: float = 1e-11
    rtol: float = 1e-11
    subdivisions: int = 10000
    panels: int = 8
    precision: str = "float64"

def integrated_variance(v, tau, kappa, forcing):
    # Integral of E[v_t] with drift forcing-kappa*v, including kappa=0.
    z = kappa*tau
    if abs(z) < 1e-5:
        a = tau*(1-z/2+z*z/6-z**3/24+z**4/120)
        b = tau*tau*(.5-z/6+z*z/24-z**3/120+z**4/720)
    else:
        a = -np.expm1(-z)/kappa
        b = (tau-a)/kappa
    return v*a+forcing*b, a

def cf(u, v, tau, p, return_D=False):
    u = np.asarray(u, dtype=complex)
    if p.sigma == 0:
        iv, av = integrated_variance(v, tau, p.kappa, p.kappa*p.theta)
        D = -.5*(u*u+1j*u)*av
        value = np.exp(1j*u*p.r*tau-.5*(u*u+1j*u)*iv)
    else:
        original_u=u
        # Remove exact identities before algebra if b+d could vanish.
        u=np.where((u==0)|(u==-1j),1.+0j,u)
        b = p.kappa-p.rho*p.sigma*1j*u
        d = np.sqrt(b*b+p.sigma*p.sigma*(u*u+1j*u))
        d = np.where(d.real < 0, -d, d)
        # Rationalized b-d avoids loss of significance near zero frequency.
        bm = -p.sigma**2*(u*u+1j*u)/(b+d)
        g = bm/(b+d)
        em = np.expm1(-d*tau)
        D = bm/p.sigma**2*(-em)/(1-g*(1+em))
        C = p.kappa*p.theta/p.sigma**2*(bm*tau-2*(np.log1p(-g*(1+em))-np.log1p(-g)))
        value = np.exp(1j*u*p.r*tau+C+D*v)
        value = np.where(original_u == 0, 1.+0j, value)
        value = np.where(original_u == -1j, np.exp(p.r*tau)+0j, value)
        D = np.where((original_u == 0)|(original_u == -1j), 0.+0j, D)
    return (value, D) if return_D else value

def deterministic(case):
    p=case.p; S=case.S; K=case.K; t=case.tau
    iv, av=integrated_variance(case.v,t,p.kappa,p.kappa*p.theta)
    if iv <= 0:
        raise ValueError("zero integrated variance: Greeks not defined by this branch")
    root=np.sqrt(iv); d1=(case.x+p.r*t+iv/2)/root; d2=d1-root
    pdf=np.exp(-d1*d1/2)/np.sqrt(2*np.pi)
    nu=S*pdf*av/(2*root)
    return Estimate(float(S*ndtr(d1)-K*np.exp(-p.r*t)*ndtr(d2)),float(ndtr(d1)),
                    float(pdf/(S*root)),float(nu),float(2*np.sqrt(case.v)*nu),
                    {"route":"A", "analytic_limit":"sigma=0", "raw_unclipped":True})

def price(case, config=Quadrature()):
    if config.precision != "float64":
        raise NotImplementedError("Route A currently supports float64 only; high precision must be escalated explicitly")
    if case.tau == 0:
        if case.x == 0:
            return Estimate(max(case.S-case.K,0),np.nan,np.nan,np.nan,np.nan,{"route":"A","terminal_ATM":True})
        return Estimate(max(case.S-case.K,0),float(case.x>0),0.,0.,0.,{"route":"A","terminal":True})
    if case.p.sigma == 0: return deterministic(case)
    if case.v < 0 or case.tau < 0: raise ValueError("negative state")
    p=case.p; m=np.exp(case.x); discount=np.exp(-p.r*case.tau)
    iv,a=integrated_variance(case.v,case.tau,p.kappa,p.kappa*p.theta)
    ivs,astock=integrated_variance(case.v,case.tau,p.kappa-p.rho*p.sigma,p.kappa*p.theta)
    def integrand(u):
        if u == 0:
            return np.array([case.x+p.r*case.tau+.5*ivs, case.x+p.r*case.tau-.5*iv,
                             1/m, m*.5*astock+discount*.5*a])
        f1,D1=cf(u-1j,case.v,case.tau,p,True)
        f2,D2=cf(u,case.v,case.tau,p,True)
        phase=np.exp(1j*u*case.x)
        z1=phase*f1*discount; z2=phase*f2
        return np.array([z1.imag/u,z2.imag/u,z1.real/m,
                         (m*z1*D1-discount*z2*D2).imag/u],dtype=float)
    values,error,info=quad_vec(integrand,0.,config.cutoff,epsabs=config.atol,
        epsrel=config.rtol,limit=config.subdivisions,points=np.linspace(0,config.cutoff,config.panels+1)[1:-1],full_output=True)
    P1=.5+values[0]/np.pi; P2=.5+values[1]/np.pi
    nu=case.K*values[3]/np.pi
    return Estimate(float(case.K*(m*P1-discount*P2)),float(P1),float(values[2]/(np.pi*case.K)),
        float(nu),float(2*np.sqrt(case.v)*nu),{"route":"A","config":asdict(config),
        "quadrature_error_vector_norm":float(error),"success":bool(info.success),
        "status":int(info.status),"message":info.message,"evaluations":int(info.neval),
        "P1":float(P1),"P2":float(P2),"raw_unclipped":True,"tail_error_certified":False})
