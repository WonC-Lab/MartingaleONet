"""Additional boundary tail/term extension diagnostics; never repairs stored rows."""
from pathlib import Path
from . import route_a as A, route_b as B, certification_grid as grid
from .types import Case
from .certify import dump

def run(output="reference"):
    rows=[]
    for i in [0,4]:
        c=Case(0,0,.001,1,grid.REGIMES[i],f"escalation_R{i}")
        for U in [2048,4096,8192,16384,32768,65536]:
            e=A.price(c,A.Quadrature(cutoff=U,atol=1e-11,rtol=1e-11))
            rows.append(dict(input=c.row(),route="A",estimate=e.row()))
        for L in [16,32]:
            for N in [4096,8192,16384,32768,65536]:
                e=B.price(c,B.COS(N,L))
                rows.append(dict(input=c.row(),route="B",estimate=e.row()))
    dump(Path(output)/"BOUNDARY_ESCALATION.json",dict(rows=rows,
         gate_impact="diagnostic only; original failed rows retained; no certification upgrade"))
    return rows

if __name__=="__main__":run()
