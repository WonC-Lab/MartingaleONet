"""Fixed, input-only partition of Domain v1. No outcome-dependent selection."""
from reference.certification_grid import full, deterministic

VERSION="phase1b2-partition-v1"
def parameter_core(p):
    return (.5<=p.kappa<=4 and .02<=p.theta<=.12 and .1<=p.sigma<=.8
            and -.9<=p.rho<=-.1 and 0<=p.r<=.08)

def classify(c):
    if not parameter_core(c.p) or c.v==0 or c.tau<1/252 or c.tau>2:
        return "CHALLENGE"
    if -.7<=c.x<=.7 and .01<=c.v<=.16 and 1/252<=c.tau<=2:
        return "CORE"
    if -1.2<=c.x<=1.2 and 0<c.v<=.25:
        return "COLLAR"
    return "CHALLENGE"

def mandatory_core():return [c for c in deterministic() if classify(c)=="CORE"]
def all_core():return [c for c in full() if classify(c)=="CORE"]
