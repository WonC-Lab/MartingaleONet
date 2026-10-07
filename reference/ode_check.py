"""Direct numerical affine ODE: independent third CF validation, not a third price engine."""
import numpy as np
from scipy.integrate import solve_ivp

def cf(u,v,tau,p):
    def rhs(t,y):
        d,c=y
        return [-(u*u+1j*u)/2+(1j*p.rho*p.sigma*u-p.kappa)*d+p.sigma**2*d*d/2,
                p.kappa*p.theta*d]
    sol=solve_ivp(rhs,(0,tau),[0j,0j],method="DOP853",rtol=1e-11,atol=1e-13)
    if not sol.success: raise ArithmeticError(sol.message)
    d,c=sol.y[:,-1]
    return np.exp(1j*u*p.r*tau+c+v*d)
