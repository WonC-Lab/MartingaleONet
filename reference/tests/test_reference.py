from dataclasses import replace
import json
import math
import numpy as np
import pytest
from scipy.special import ndtr
from reference.types import Case, Parameters
from reference import route_a as A, route_b as B, ode_check, certification_grid as grid
from reference.derivatives import studies, strike_check
from reference.certify import save_npz, dump

@pytest.mark.parametrize("p",grid.REGIMES)
def test_cf_identities_and_ode(p):
    for f in (A.cf,B.cf):
        assert f(0,.04,1,p)==1
        assert abs(f(-1j,.04,1,p)-math.exp(p.r))<1e-13
        assert abs(f(-3,.04,1,p)-np.conj(f(3,.04,1,p)))<1e-13
        assert abs(f(3,.04,1,p)-ode_check.cf(3,.04,1,p))<1e-9
    assert abs(ode_check.cf(-1j,.04,1,p)-math.exp(p.r))<1e-11

@pytest.mark.parametrize("m",[.8,.9,1,1.1,1.2])
@pytest.mark.parametrize("tau",[.01,.5,2])
def test_off_atm_regression(m,tau):
    c=Case(math.log(m),.04,tau)
    a=A.price(c,A.Quadrature(cutoff=2048));b=B.price(c,B.COS(4096,32))
    assert abs(a.price-b.price)<1e-8
    assert abs(a.Delta-b.Delta)<2e-6
    assert abs(a.Gamma-b.Gamma)<2e-5
    assert abs(a.Vv-b.Vv)<2e-5
    for e in (a,b):
        assert max(c.S-c.K*math.exp(-c.p.r*tau),0)-1e-8<=e.price<=c.S+1e-8
        assert -2e-6<=e.Delta<=1+2e-6
        assert e.Gamma>=-2e-5

def test_known_deterministic_variance_bs():
    c=Case(p=Parameters(2,.04,0,-.7,.03))
    # Independent BS ATM with constant variance: d1=(r+v/2)/sqrt(v).
    expected=ndtr(.25)-math.exp(-.03)*ndtr(.05)
    assert abs(A.price(c).price-expected)<1e-13
    assert abs(B.price(c,B.COS(4096,16)).price-expected)<1e-12
    c=replace(c,v=.09)
    iv=.04+(.09-.04)*(1-math.exp(-2))/2
    d1=(.03+iv/2)/math.sqrt(iv)
    expected=ndtr(d1)-math.exp(-.03)*ndtr(d1-math.sqrt(iv))
    assert abs(A.price(c).price-expected)<1e-13

def test_homogeneity_derivatives_and_strike():
    c=Case();a=A.price(c);b=B.price(c,B.COS(4096,32))
    for K in [50,100,200]:
        assert abs(A.price(replace(c,K=K)).price/K-a.price)<1e-13
        assert abs(B.price(replace(c,K=K),B.COS(4096,32)).price/K-b.price)<1e-13
    fd=studies(c,b)
    for key in ["Delta","Gamma","Vv"]:
        assert abs(fd[-1][key]-getattr(a,key))<2e-6
        assert abs(fd[-1][key]-fd[-2][key])<2e-6
    sk=strike_check(c,b)
    assert abs(sk["V_K"]-(b.price-c.S*b.Delta)/c.K)<2e-7
    assert abs(sk["V_KK"]-(c.S/c.K)**2*b.Gamma)<2e-6
    assert -math.exp(-c.p.r)<=sk["V_K"]<=0
    assert sk["V_KK"]>=0

def test_determinism_grid_and_serialization(tmp_path):
    assert grid.full()==grid.full()
    assert len(grid.full())==5840
    assert A.price(Case()).row()==A.price(Case()).row()
    assert B.price(Case()).row()==B.price(Case()).row()
    rows=[{**Case().row(),"status":"FAIL","raw_negative":-1e-12,"relative_price_gap":float("nan")}]
    save_npz(tmp_path/"raw.npz",rows);dump(tmp_path/"raw.json",rows)
    with np.load(tmp_path/"raw.npz",allow_pickle=False) as data:
        assert data["raw_negative"][0]==-1e-12
        assert np.isnan(data["relative_price_gap"][0])
    assert json.loads((tmp_path/"raw.json").read_text())[0]["relative_price_gap"] is None

def test_failure_preserved_and_terminal():
    with pytest.raises(NotImplementedError): A.price(Case(),A.Quadrature(precision="float80"))
    z=A.price(Case(tau=0))
    assert z.price==0 and math.isnan(z.Gamma)
    with pytest.raises(ValueError):B.price(Case(v=-.1))

def test_parameter_and_frequency_continuity():
    p=Parameters();perturb=replace(p,rho=p.rho+1e-7)
    u=np.linspace(0,100,2001)
    a=A.cf(u,.04,5,p);b=B.cf(u,.04,5,p)
    assert np.max(abs(a-b))<1e-12
    for f in (A.cf,B.cf):
        assert abs(f(3,.04,5,p)-f(3,.04,5,perturb))<1e-7

def test_positive_rho_stock_moment_singular_algebra():
    p=Parameters(.2,.04,1.2,.5,.03)
    # SciPy's adaptive step initialization deliberately uses subnormals.
    # Raise only on invalid/divide/overflow, including production CF algebra.
    with np.errstate(invalid="raise",divide="raise",over="raise"):
        for f in (A.cf,B.cf):
            assert f(0,.04,5,p)==1
            assert abs(f(-1j,.04,5,p)-math.exp(.15))<1e-13
            for u in [.0001-1j,1-1j,2.]:
                assert abs(f(u,.04,5,p)-ode_check.cf(u,.04,5,p))<1e-9
