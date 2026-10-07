import hashlib
from dataclasses import replace
import pytest
from reference.types import Case,Parameters
from reference_v2.high_precision import Integrator as Direct,MPConfig,num,cf
from reference_v3.mp import Integrator
from reference_v3.provenance import verified
from reference_v3.boundary import plan
from reference_v2.domains import all_core

@pytest.mark.parametrize('initial',[0,.01,.04])
def test_affine_variance_cache_matches_independent_cf(initial):
    c=Case(.1,initial,.5,1,Parameters(),'cache_regression')
    obj=Integrator(c,MPConfig(50,64,24,.2));ctx=obj.ctx
    for v in [ctx.mpf('0'),ctx.mpf('.00001'),ctx.mpf('.04'),ctx.mpf('.08')]:
        cached=obj.spectrum(v)
        for i in [0,len(obj.u)//2,len(obj.u)-1]:
            expected,D=cf(ctx,obj.u[i]-ctx.j/2,v,c.tau,c.p,True)
            assert abs(cached[i][0]-expected)<ctx.mpf('1e-45')
            assert abs(cached[i][1]-D)<ctx.mpf('1e-45')
        direct=Direct(c,obj.cfg).values(v=v)
        assert max(abs(obj.values(v=v)[f]-direct[f]) for f in ['price','Delta','Gamma','Vv'])<ctx.mpf('1e-44')

def test_historical_eol_transport_only(tmp_path):
    p=tmp_path/'a.py';source=b'a=1\r\nb=2\r\n';expected=hashlib.sha256(source).hexdigest()
    p.write_bytes(source);assert verified(p,expected)=='BYTE_IDENTICAL'
    p.write_bytes(source.replace(b'\r\n',b'\n'));assert verified(p,expected)=='EOL_TRANSPORT_ONLY'
    p.write_bytes(b'a=2\nb=2\n')
    with pytest.raises(RuntimeError):verified(p,expected)

def test_catalog_and_objective_boundary_are_not_filtered():
    assert len(all_core())==1734
    boundary=plan();assert len(boundary)==600
    assert sum(c.v==0 for c in boundary)==210
    assert all(c.v==0 or c.v==.25 or abs(c.x)==1.2 for c in boundary)

def test_immutable_catalog_rejects_same_count_substitution():
    import json
    from reference_v3.reuse import validate
    rows=[dict(c.row(),status='PASS') for c in all_core()]
    validate('\n'.join(json.dumps(r) for r in rows).encode())
    rows[0]['tau']=3.
    with pytest.raises(RuntimeError,match='original 1734'):validate('\n'.join(json.dumps(r) for r in rows).encode())

def test_quantlib_exact_zero_is_not_silently_floored():
    ql=pytest.importorskip('QuantLib')
    assert ql.__version__=='1.41'
    from reference_v2.external import cases,evaluate
    with pytest.raises(RuntimeError,match='invalid value'):evaluate(cases()[-1])

def test_finite_dirichlet_trace_does_not_certify_unused_greeks(monkeypatch):
    from reference import route_b as B
    from reference_v3 import mp
    c=Case(1.2,.25,1,1,Parameters(),'finite_boundary')
    b=B.price(c,B.COS(4096,32))
    r=dict(c.row(),training_required_boundary=True,domain='COLLAR',failure_flags=[])
    r.update({'route_B_'+f:getattr(b,f) for f in ['price','Delta','Gamma','Vv']})
    def forbidden(*args,**kwargs):raise AssertionError('FD labels are not used by this Dirichlet trace')
    monkeypatch.setattr(mp,'finite_differences',forbidden)
    evidence=mp.worker(r)
    assert evidence['status']=='NUMERICALLY_RESOLVED'
    assert evidence['required_fields']==['price'] and evidence['MP_FD']['rows']==[]
    assert all(evidence['component_status'][f]=='UNRESOLVED' for f in ['Delta','Gamma','Vv'])

def test_evidence_bundle_resumes_without_loose_files_and_rejects_corruption(tmp_path,monkeypatch):
    import json
    from reference_v3 import reuse
    clone=tmp_path/'clone';folder=clone/'reference_v3/immutable';folder.mkdir(parents=True)
    name='reference_v3/mp_cases/revision/point.json';source=clone/name
    source.parent.mkdir(parents=True);source.write_bytes(b'{"status":"NUMERICALLY_RESOLVED"}\n')
    manifest=folder/'LOCAL_EVIDENCE_MANIFEST.json'
    manifest.write_text(json.dumps({'files':{name:reuse.sha(source.read_bytes())}}))
    monkeypatch.setattr(reuse,'ROOT',clone)
    reuse.pack_evidence_bundle();source.unlink()
    output=tmp_path/'output';output.mkdir()
    reuse.import_evidence(output)
    target=output/'mp_cases/revision/point.json'
    assert target.read_bytes()==b'{"status":"NUMERICALLY_RESOLVED"}\n'
    reuse.import_evidence(output)
    target.write_bytes(b'changed')
    with pytest.raises(RuntimeError,match='checkpoint differs'):reuse.import_evidence(output)
    manifest.with_suffix('.zip').write_bytes(b'corrupted')
    empty=tmp_path/'empty';empty.mkdir()
    with pytest.raises(RuntimeError,match='bundle SHA'):reuse.import_evidence(empty)
    assert list(empty.iterdir())==[]

def test_missing_evidence_has_actionable_error_without_repricing(tmp_path,monkeypatch):
    import json
    from reference_v3 import reuse
    folder=tmp_path/'reference_v3/immutable';folder.mkdir(parents=True)
    (folder/'LOCAL_EVIDENCE_MANIFEST.json').write_text(json.dumps({'files':{'reference_v3/mp_cases/missing.json':'0'*64}}))
    monkeypatch.setattr(reuse,'ROOT',tmp_path)
    with pytest.raises(RuntimeError,match='CORE remains reused; no full sweep'):
        reuse.import_evidence(tmp_path/'output')
