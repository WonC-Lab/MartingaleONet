"""Domain v1 / grid v1.1: predeclared Sobol replacement for random coverage."""
import math
from scipy.stats import qmc
from .types import Case, Parameters

VERSION="domain-v1-grid-v1.1-sobol4101"
REGIMES=[Parameters(),Parameters(1,.04,math.sqrt(.08),-.7,.03),
 Parameters(1,.04,.27,-.7,.03),Parameters(1,.04,.30,-.7,.03),
 Parameters(.5,.04,1.2,-.99,.03),Parameters(4,.12,.8,-.1,0)]
def deterministic():
    return [Case(x,v,t,1,p,f"R{i}") for i,p in enumerate(REGIMES)
            for x in [-1.2,-.7,-.1,0,.1,.7,1.2] for v in [0,.005,.01,.04,.25]
            for t in [.001,1/252,.01,.1,.5,1,2,5]]

def sobol():
    # 256 parameter blocks x 16 state queries; no Feller filtering.
    ps=qmc.Sobol(5,scramble=True,seed=4101).random_base2(8)
    zs=qmc.Sobol(3,scramble=True,seed=4102).random_base2(12)
    out=[]
    for i,q in enumerate(ps):
        p=Parameters(.5+3.5*q[0],.02+.10*q[1],.1+.7*q[2],-.9+.8*q[3],.08*q[4])
        for j in range(16):
            z=zs[i*16+j]
            out.append(Case(-1.2+2.4*z[0],.25*z[1],1/252+(2-1/252)*z[2],1,p,f"sobol_{i}_{j}"))
    return out

def challenges():
    qs=qmc.Sobol(8,scramble=True,seed=4103).random_base2(6)
    out=[]
    for i,q in enumerate(qs):
        p=Parameters(.2+5.8*q[0],.005+.195*q[1],.8+.4*q[2],
                     -.99+.09*q[3] if i%2==0 else .5*q[3],.08*q[4])
        out.append(Case(-1.2+2.4*q[5],0 if i%8==0 else .25*q[6],
                        .001 if i%4==0 else 3+2*q[7],1,p,f"challenge_{i}"))
    return out

def full(): return deterministic()+sobol()+challenges()

def local():
    # Explicit small diagnostic slice, never substituted for the 256/full gate.
    out=[Case(math.log(m),.04,t,1,REGIMES[0],"offATM")
         for m in [.8,.9,1,1.1,1.2] for t in [.01,.5,2]]
    out += [Case(x,v,t,1,REGIMES[i],f"local_R{i}")
            for i,x,v,t in [(1,0,.04,1),(2,0,.04,1),(3,0,.04,1),
                           (4,0,0,.001),(4,-1.2,.005,5),(4,1.2,.25,.001),
                           (5,0,.25,2),(0,0,0,.001),(0,-1.2,.01,.001),(0,1.2,.25,5)]]
    return out
