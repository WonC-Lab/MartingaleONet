"""Synthetic interrupt/resume tests; production inputs are never priced."""
import copy
from decimal import Decimal
import hashlib
import json
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from reference_v6 import mp_backend as backend
from reference_v6 import resume_support as support
from reference_v6 import run_boundary_certification as runner

ROW={'case_id':'synthetic_only','x':'.13','v':'0','tau':'.73','K':'1','kappa':'1.7','theta':'.05','sigma':'.25','rho':'-.4','r':'0'}


def legacy(module_path):
    text=subprocess.check_output(['git','show',support.LEGACY_COMMIT+':reference_v6/'+module_path],cwd=runner.ROOT.parent,text=True)
    module=types.ModuleType('synthetic_legacy');module.__file__=str(runner.ROOT/module_path);exec(compile(text,module.__file__,'exec'),module.__dict__);return module


def fake(row,route,cfg,coords,tick=lambda:None,saved=None,checkpoint=lambda z:None):
    # Smooth synthetic affine solution: c_tau=kappa*theta, nu=1, r=0.
    values=[]
    for x,v,t in coords:
        c=Decimal('.2')+Decimal('.4')*Decimal(str(x)).exp()+Decimal(str(v))+Decimal(row['kappa'])*Decimal(row['theta'])*Decimal(str(t))
        values.append({'values':{'c':str(c),'Delta':'.4','nu':'1'},'roundoff':dict.fromkeys(backend.FIELDS,'1e-100')})
    return {'route':route,'config':cfg,'coordinates':[list(map(str,q)) for q in coords],
            'results':values,'nodes':1,'actual_bit_precision':400}


class ResumeTests(unittest.TestCase):
    def test_transient_replaced_lease_is_retried_and_missing_required_stops(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'RUNNER_LEASE.json'
            with patch.object(Path,'read_text',side_effect=[FileNotFoundError(),json.dumps({'session_id':'a','active':True})]),patch.object(support.time,'sleep'):
                self.assertEqual(support.read_lease(path)['session_id'],'a')
            with patch.object(Path,'read_text',side_effect=FileNotFoundError()),patch.object(support.time,'sleep'):
                with self.assertRaises(support.LeaseUnavailable):support.read_lease(path)

    def test_parent_verified_catalog_blocks_kernel_when_drive_hides_completed_file(self):
        with tempfile.TemporaryDirectory() as td:
            cfg={'N':64,'L':16,'dps':50};coords=[('.13',0,'.73')];key=support.key('E2',cfg,coords)
            obj=runner.CaseRunner(ROW,td,time.monotonic()+100,verified_catalog={key:'previously_verified_bytes'})
            with patch.object(runner,'evaluate',side_effect=AssertionError('recomputed parent-verified key')) as kernel:
                with self.assertRaises(runner.ResourceStop):obj.raw('E2',cfg,coords)
                self.assertEqual(kernel.call_count,0)

    def test_fresh_worker_process_restores_unfinished_journals(self):
        with tempfile.TemporaryDirectory() as td:
            completed=[]
            def interrupted(*args,**kwargs):
                if len(completed)==25:raise runner.ResourceStop('synthetic parent interrupted')
                completed.append(support.key(args[1],args[2],args[3]));return fake(*args,**kwargs)
            with patch.object(runner,'evaluate',side_effect=interrupted):
                with self.assertRaises(runner.ResourceStop):runner.CaseRunner(ROW,td,time.monotonic()+100).run()
            code='''import json,sys,time
from reference_v6 import run_boundary_certification as r,resume_support as s
from reference_v6.test_resume import ROW,fake
completed=set(json.loads(sys.argv[2]))
def kernel(*args,**kwargs):
    assert s.key(args[1],args[2],args[3]) not in completed, "worker recomputed completed key"
    return fake(*args,**kwargs)
r.evaluate=kernel
z=r.worker(ROW,sys.argv[1],time.monotonic()+100)
assert z['status']=='PASS', z
print('FRESH_WORKER_RESUME_PASS')
'''
            out=subprocess.check_output([sys.executable,'-c',code,td,json.dumps(completed)],cwd=runner.ROOT.parent,text=True)
            self.assertIn('FRESH_WORKER_RESUME_PASS',out)

    def test_real_tree_plan_has_zero_kernel_calls_and_smoke_at_most_one(self):
        from reference_v6 import resume_plan as p
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);production=root/'production';report=root/'plan.json'
            a=runner.CaseRunner(ROW,production,time.monotonic()+100)
            cfg={'dps':50,'N':4096,'L':16};coords=[('.13','0','.73')]
            with patch.object(runner,'evaluate',side_effect=fake):a.raw('E2',cfg,coords)
            before={str(q.relative_to(production)):q.read_bytes() for q in production.rglob('*') if q.is_file()}
            with patch.object(p,'validate',return_value={}),patch.object(p,'rows',return_value=[ROW]),patch.object(runner,'evaluate',side_effect=AssertionError('plan priced')) as kernel:
                z=p.plan(production,report)
                self.assertEqual(kernel.call_count,0)
            self.assertEqual(z['cases'][0]['reusable_E2'],1)
            self.assertIsNotNone(z['cases'][0]['first_genuinely_missing_key'])
            with patch.object(p,'validate',return_value={}),patch.object(p,'rows',return_value=[ROW]),patch.object(runner,'evaluate',side_effect=fake) as kernel:
                z=p.smoke(production,report,ROW['case_id'],root/'smoke')
                self.assertEqual(kernel.call_count,1);self.assertEqual(z['kernel_calls'],1)
            self.assertEqual(before,{str(q.relative_to(production)):q.read_bytes() for q in production.rglob('*') if q.is_file()})

    def setUp(self):
        self.capture=contextlib.redirect_stdout(io.StringIO());self.capture.__enter__()
    def tearDown(self):self.capture.__exit__(None,None,None)
    def test_completed_configuration_skips_backend_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            r=runner.CaseRunner(ROW,td,time.monotonic()+100)
            cfg={'dps':50,'N':64,'L':16};coords=[('.13',0,'.73')]
            with patch.object(runner,'evaluate',side_effect=fake):r.raw('E2',cfg,coords)
            path=r.output/'raw'/(support.key('E2',cfg,coords)+'.json');before=path.read_bytes()
            with patch.object(runner,'evaluate',side_effect=AssertionError('completed evaluation recomputed')):
                q=runner.CaseRunner(ROW,td,time.monotonic()+100);q.raw('E2',cfg,coords)
            self.assertEqual(q.stats['cached_evaluations'],1);self.assertEqual(path.read_bytes(),before)

    def test_convergence_position_and_complete_operation_resume(self):
        with tempfile.TemporaryDirectory() as td:
            calls=[];coords=[('.13',0,'.73')];target=dict.fromkeys(backend.FIELDS,Decimal('1e-5'))
            def interrupted(*args,**kwargs):
                if len(calls)==4:raise runner.ResourceStop('synthetic interruption')
                calls.append(support.key(args[1],args[2],args[3]));return fake(*args,**kwargs)
            a=runner.CaseRunner(ROW,td,time.monotonic()+100)
            with patch.object(runner,'evaluate',side_effect=interrupted):
                with self.assertRaises(runner.ResourceStop):a.converge('E1',coords,target)
            completed=set(calls);subsequent=[]
            def continued(*args,**kwargs):
                k=support.key(args[1],args[2],args[3]);self.assertNotIn(k,completed);subsequent.append(k);return fake(*args,**kwargs)
            b=runner.CaseRunner(ROW,td,time.monotonic()+100)
            with patch.object(runner,'evaluate',side_effect=continued):result=b.converge('E1',coords,target)
            # Same final config is shared by degree/precision axes and the
            # final return. Those three lookups are required, not a replay.
            self.assertEqual(b.stats['cached_evaluations'],3)
            c=runner.CaseRunner(ROW,td,time.monotonic()+100)
            with patch.object(c,'raw',side_effect=AssertionError('completed operation replayed')):
                self.assertEqual(c.converge('E1',coords,target),result)

    def test_full_case_interrupt_matches_legacy_science(self):
        old=legacy('run_boundary_certification.py');old.evaluate=fake
        with tempfile.TemporaryDirectory() as td:
            expected=old.CaseRunner(ROW,Path(td)/'old',time.monotonic()+100).run()
            calls=[]
            def interrupted(*args,**kwargs):
                if len(calls)==25:raise runner.ResourceStop('synthetic interruption')
                calls.append(support.key(args[1],args[2],args[3]));return fake(*args,**kwargs)
            with patch.object(runner,'evaluate',side_effect=interrupted):
                with self.assertRaises(runner.ResourceStop):runner.CaseRunner(ROW,Path(td)/'new',time.monotonic()+100).run()
            completed=set(calls)
            def continued(*args,**kwargs):
                self.assertNotIn(support.key(args[1],args[2],args[3]),completed);return fake(*args,**kwargs)
            with patch.object(runner,'evaluate',side_effect=continued):actual=runner.CaseRunner(ROW,Path(td)/'new',time.monotonic()+100).run()
            expected.pop('stats');actual.pop('stats');self.assertEqual(runner.serial(actual),runner.serial(expected));self.assertEqual(actual['status'],'PASS')

    def test_legacy_partial_sums_both_estimators_no_replayed_cf(self):
        old=legacy('mp_backend.py');coords=[('.13','.05','.73')]
        for route,cfg in [('E1',{'dps':50,'degree':24,'cutoff':256,'span':'.75'}),('E2',{'dps':50,'N':512,'L':16})]:
            checkpoints=[];ticks=[]
            def stop():
                ticks.append(1)
                if len(ticks)==3:raise runner.ResourceStop('synthetic interruption')
            with self.assertRaises(runner.ResourceStop):old.evaluate(ROW,route,cfg,coords,tick=stop,checkpoint=checkpoints.append)
            saved=checkpoints[-1];self.assertEqual(saved['nodes'],256)
            expected=old.evaluate(ROW,route,cfg,coords)
            name='cf' if route=='E1' else 'hyperbolic_cf'
            with patch.object(backend,name,wraps=getattr(backend,name)) as tracked:
                actual=backend.evaluate(ROW,route,cfg,coords,saved=saved)
            self.assertEqual(actual,expected)
            self.assertEqual(tracked.call_count,expected['nodes']-256)

    def test_legacy_identity_accepted_unknown_hash_rejected(self):
        old={'protocol_SHA256':'a','input_SHA256':'b','executor_SHA256':support.LEGACY_EXECUTOR,'CORE_recomputed':0,'old_boundary_recomputed':0}
        current={**old,'executor_SHA256':runner.fingerprint()}
        self.assertTrue(support.compatible(old,current))
        changed={**old,'executor_SHA256':{**support.LEGACY_EXECUTOR,'mp_backend.py':'unknown'}}
        self.assertFalse(support.compatible(changed,current))
        self.assertFalse(support.compatible({**old,'input_SHA256':'different'},current))

    def test_old_unfinished_case_hydrates_to_first_missing_without_pricing(self):
        from reference_v6.hydrate_legacy import Hydrator,Missing
        old=legacy('run_boundary_certification.py');calls=[]
        def interrupted(*args,**kwargs):
            if len(calls)==25:raise runner.ResourceStop('synthetic legacy interruption')
            calls.append(support.key(args[1],args[2],args[3]));return fake(*args,**kwargs)
        old.evaluate=interrupted
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(runner.ResourceStop):old.CaseRunner(ROW,td,time.monotonic()+100).run()
            files={p:p.read_bytes() for p in Path(td).rglob('*.json')}
            with patch.object(runner,'evaluate',side_effect=AssertionError('hydration priced input')) as blocked:
                with self.assertRaises(Missing) as stopped:Hydrator(ROW,td,time.monotonic()+100).run()
            self.assertNotIn(stopped.exception.record['key'],set(calls));self.assertEqual(blocked.call_count,0)
            self.assertTrue(all(p.read_bytes()==data for p,data in files.items()))
            started=[]
            def continued(*args,**kwargs):
                k=support.key(args[1],args[2],args[3]);self.assertNotIn(k,set(calls));started.append(k);return fake(*args,**kwargs)
            with patch.object(runner,'evaluate',side_effect=continued):runner.CaseRunner(ROW,td,time.monotonic()+100).run()
            self.assertEqual(started[0],stopped.exception.record['key'])

    def test_active_drive_lease_blocks_another_session(self):
        with tempfile.TemporaryDirectory() as td:
            with support.drive_lease(td,'synthetic-a'):
                with self.assertRaises(RuntimeError):
                    with support.drive_lease(td,'synthetic-b'):self.fail('another session accepted active lease')

    def test_catalogued_completed_checkpoint_not_visible_is_not_recomputed(self):
        with tempfile.TemporaryDirectory() as td:
            cfg={'dps':50,'N':64,'L':16};coords=[('.13',0,'.73')]
            a=runner.CaseRunner(ROW,td,time.monotonic()+100)
            with patch.object(runner,'evaluate',side_effect=fake):a.raw('E2',cfg,coords)
            b=runner.CaseRunner(ROW,td,time.monotonic()+100);original=Path.exists
            def hidden(path):
                if path.parent.name=='raw' and path.suffix=='.json':return False
                return original(path)
            with patch.object(Path,'exists',new=hidden),patch.object(runner,'evaluate',side_effect=AssertionError('missing known checkpoint recomputed')):
                with self.assertRaises(runner.ResourceStop):b.raw('E2',cfg,coords)

    def test_simultaneous_same_runtime_writer_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with support.local_run_lock(td):
                with self.assertRaises(RuntimeError):
                    with support.local_run_lock(td):self.fail('second writer acquired lock')


if __name__=='__main__':unittest.main()
