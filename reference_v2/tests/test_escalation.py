from dataclasses import replace
import math
import pytest
from reference.types import Case,Parameters
from reference import route_a,ode_check
from reference.certification_grid import full
from reference_v2.domains import classify,mandatory_core
from reference_v2.high_precision import context,cf,evaluate,MPConfig,gaussian_rule,finite_differences
from reference_v2.external import mapping

def test_partition_exact_and_frozen():
    from collections import Counter
    assert Counter(classify(c) for c in full())=={"CORE":1734,"COLLAR":3202,"CHALLENGE":904}
    assert len(mandatory_core())==300
    assert classify(Case(v=0))=="CHALLENGE"
    assert classify(Case(x=.8))=="COLLAR"
    assert classify(Case(v=.01,tau=1/252,x=.7))=="CORE"

@pytest.mark.parametrize("dps",[50,80,120])
def test_mp_cf_and_true_nodes(dps):
    ctx=context(dps);p=Parameters()
    assert cf(ctx,0,.04,1,p)==1
    assert abs(cf(ctx,-ctx.j,.04,1,p)-ctx.exp(ctx.mpf('.03')))<ctx.mpf('1e-45')
    nodes,weights=gaussian_rule(dps,16)
    assert abs(ctx.fsum(weights)-2)<ctx.mpf('1e-45')
    assert abs(complex(cf(ctx,2-ctx.j/2,.04,1,p))-ode_check.cf(2-.5j,.04,1,p))<1e-10

def test_mp_bs_and_precision_convergence():
    p=Parameters(2,.04,0,-.7,.03);c=Case(p=p)
    ctx=context(80);normal=lambda x:(1+ctx.erf(x/ctx.sqrt(2)))/2
    exact=normal(ctx.mpf('.25'))-ctx.exp(ctx.mpf('-.03'))*normal(ctx.mpf('.05'))
    estimates=[evaluate(c,MPConfig(d,128,48,.1)) for d in [50,80,120]]
    vals=[ctx.mpf(e['values']['price']) for e in estimates]
    assert abs(vals[-1]-exact)<ctx.mpf('1e-25')
    assert abs(vals[0]-vals[-1])<ctx.mpf('1e-40')

def test_mp_fd_physical_spot_and_right_variance():
    c=Case();r=finite_differences(c,MPConfig(50,256,32,.1),steps=['.0025','.00125','.000625'])
    ctx=context(50);base=ctx.mpf(r['base']['Gamma'])
    assert abs(ctx.mpf(r['rows'][-1]['values']['Gamma5'])-base)<ctx.mpf('2e-7')
    r=finite_differences(Case(v=0,tau=.01),MPConfig(50,512,16,.04),steps=['.0001'])
    assert r['rows'][0]['variance_offsets']==[0,1,2,3,4]

@pytest.mark.parametrize("tau",[.001,1/252,.01,1,2])
def test_exact_external_time_change(tau):
    c=Case(tau=tau);mapped,info=mapping(c)
    # Equality of CFs proves aligned transition distributions at declared inputs.
    for u in [1,3,7]:
        assert abs(route_a.cf(u,c.v,c.tau,c.p)-route_a.cf(u,mapped.v,mapped.tau,mapped.p))<1e-12
    assert abs(c.p.r*c.tau-mapped.p.r*mapped.tau)<1e-15

@pytest.mark.parametrize("ratio",[.8,.9,1.,1.1,1.2])
def test_mp_off_atm_prefactor(ratio):
    c=Case(x=math.log(ratio),tau=.5,p=Parameters(2,.04,0,-.7,.03))
    ctx=context(80);S=ctx.mpf(str(c.S));t=ctx.mpf('.5');vol=ctx.mpf('.2')
    d1=(ctx.log(S)+ctx.mpf('.05')*t)/(vol*ctx.sqrt(t));d2=d1-vol*ctx.sqrt(t)
    normal=lambda z:(1+ctx.erf(z/ctx.sqrt(2)))/2
    known=S*normal(d1)-ctx.exp(-ctx.mpf('.03')*t)*normal(d2)
    result=evaluate(c,MPConfig(80,512,48,.4))
    assert abs(ctx.mpf(result['values']['price'])-known)<ctx.mpf('1e-20')

def test_json_null_aggregation_preserves_failures(tmp_path):
    import json
    from pathlib import Path
    from reference_v2.workflow import ROOT,aggregate,initialize
    r=json.loads((ROOT/'reference/CERTIFICATION_RESULTS.json').read_text())['rows'][0]
    assert r['relative_price_gap'] is None
    r['domain']='CORE'
    initialize(tmp_path)
    (tmp_path/'coverage_core.jsonl').write_text(json.dumps(r)+'\n')
    result=aggregate(tmp_path)
    assert result['domains']['CORE']['evaluated_grid']==1
    assert result['domains']['CORE']['gate']=='FAIL'
    saved=json.loads((tmp_path/'CERTIFICATION_RESULTS.json').read_text())['grid_rows'][0]
    assert saved['status']=='FAIL' and saved['relative_price_gap'] is None
