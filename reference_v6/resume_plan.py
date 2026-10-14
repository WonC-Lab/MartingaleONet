"""Read the real production tree; never infer reuse from an older inventory ZIP.

Adaptive future configuration counts are unknowable before the preceding value
is computed. Report the exact first missing causal frontier, not an estimate.
All numerical work in a smoke test is confined to a fresh evidence overlay.
"""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch
from reference_v6 import run_boundary_certification as r
from reference_v6 import resume_support as s
from reference_v6.hydrate_legacy import Missing


def inventory(case):
    records=[];hashes={}
    for p in sorted((case/'raw').glob('*.json')):
        z=s.checked(p);hashes[str(p.relative_to(case))]=r.digest(p)
        partial=p.name.endswith('.partial.json')
        key=p.name.split('.')[0]
        if not partial and s.key(z['route'],z['config'],z['coordinates'])!=key:
            raise RuntimeError('Raw cache key mismatch: '+str(p))
        records.append({'key':key,'partial':partial,'route':z.get('route'),
                        'config':z.get('config'),'coordinates':z.get('coordinates'),
                        'nodes':z.get('nodes'),'elapsed_seconds':z.get('elapsed_seconds')})
    for p in sorted((case/'resume').glob('*.json')):
        s.checked(p);hashes[str(p.relative_to(case))]=r.digest(p)
    return records,hashes


def copy_metadata(case,overlay):
    dest=overlay/'cases'/case.name;dest.mkdir(parents=True)
    for p in case.glob('*.json'):shutil.copy2(p,dest/p.name)
    if (case/'resume').exists():shutil.copytree(case/'resume',dest/'resume')


class Probe(r.CaseRunner):
    def __init__(self,row,overlay,source):
        self.source=Path(source)/'cases'/row['case_id']
        super().__init__(row,overlay,time.monotonic()+r.P['stopping']['batch_wall_seconds'])
    def event(self,*args,**kwargs):pass
    def raw(self,route,cfg,coords):
        key=s.key(route,cfg,coords);p=self.source/'raw'/(key+'.json')
        if not p.exists():
            partial=p.with_suffix('.partial.json')
            z=s.checked(partial) if partial.exists() else None
            raise Missing({'key':key,'route':route,'config':cfg,
                           'coordinates':[list(map(str,q)) for q in coords],
                           'partial_resumable':z is not None,'resumed_nodes':z['nodes'] if z else 0})
        previous=self.output
        try:
            self.output=self.source
            return super().raw(route,cfg,coords)
        finally:self.output=previous


def rows():
    return [json.loads(x,parse_float=str,parse_int=str) for x in
            (r.ROOT/'BOUNDARY_BLINDED_INPUTS.jsonl').read_text().splitlines()]


def validate(output):
    receipt=r.policy.verify_freeze(r.ROOT)
    old=json.loads((output/'RUN_IDENTITY.json').read_text())
    current={'protocol_SHA256':receipt['protocol_SHA256'],
             'input_SHA256':receipt['blinded_input_SHA256'],'executor_SHA256':r.fingerprint(),
             'CORE_recomputed':0,'old_boundary_recomputed':0}
    if not s.compatible(old,current):raise RuntimeError('Unknown production identity')
    if (output/'RUN_INVALID.json').exists():raise RuntimeError('Invalidated production run')
    return current


def plan(output,report_path):
    output=Path(output).resolve();identity=validate(output);result=[]
    with tempfile.TemporaryDirectory() as td,patch.object(r,'evaluate',side_effect=AssertionError('ZERO pricing plan')) as kernel:
        overlay=Path(td)
        for row in rows():
            case=output/'cases'/row['case_id'];rp=case/'RESULT.json'
            status=json.loads(rp.read_text())['status'] if rp.exists() else 'NO_RESULT'
            if status not in ['PENDING_RESOURCE_LIMIT','NO_RESULT']:continue
            records,hashes=inventory(case);complete=[z for z in records if not z['partial']]
            keys={z['key'] for z in complete};parts=[z for z in records if z['partial'] and z['key'] not in keys]
            copy_metadata(case,overlay);obj=Probe(row,overlay,output)
            item={'case_id':row['case_id'],'status':status,'reusable_E1':sum(z['route']=='E1' for z in complete),
                  'reusable_E2':sum(z['route']=='E2' for z in complete),'partial_resumable':len(parts),
                  'completed':complete,'protected_hashes':hashes,'journal_paths':sorted(str(p) for p in (case/'resume').glob('*.json')),
                  'first_genuinely_missing_key':None,'genuinely_new_at_frontier':0,
                  'adaptive_future_new_count':'UNKNOWN_UNTIL_PRECEDING_VALUES_EXIST'}
            with contextlib.redirect_stdout(io.StringIO()):
                try:obj.run();item['replay_status']='COMPLETE'
                except Missing as e:
                    item['first_genuinely_missing_key']=e.record
                    item['genuinely_new_at_frontier']=int(not e.record['partial_resumable'])
                    item['replay_status']='FRONTIER'
                except (r.ResourceStop,r.RefinementFailure) as e:item['replay_status']=str(e)
            result.append(item)
            print(json.dumps({k:v for k,v in item.items() if k not in ['completed','protected_hashes','journal_paths']},default=r.serial),flush=True)
        assert kernel.call_count==0
    report={'output_directory':str(output),'identity':identity,'production_pricing_calls':0,'cases':result}
    s.atomic(report_path,report);return report


class Smoke(Probe):
    def __init__(self,*args):super().__init__(*args);self.kernel_calls=0
    def raw(self,route,cfg,coords):
        try:return super().raw(route,cfg,coords)
        except Missing as e:
            if self.kernel_calls>=1:raise r.ResourceStop('Smoke maximum ONE missing sub-evaluation')
            self.kernel_calls+=1
            partial=self.source/'raw'/(e.record['key']+'.partial.json')
            if partial.exists():
                target=self.output/'raw'/partial.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(partial,target)
            return r.CaseRunner.raw(self,route,cfg,coords)


def smoke(output,report_path,case_id,smoke_output):
    output=Path(output).resolve();validate(output)
    report=json.loads(Path(report_path).read_text())
    if report['output_directory']!=str(output) or report['production_pricing_calls']!=0:raise RuntimeError('Wrong plan')
    item=next(z for z in report['cases'] if z['case_id']==case_id)
    case=output/'cases'/case_id
    _,before=inventory(case)
    if before!=item['protected_hashes']:raise RuntimeError('Production changed since plan; re-plan before smoke')
    target='2363ac445ab63eddd1fdfcab278b1930bf305d93e6c159872a7739ee94f6691a'
    if case_id=='v6_00_1' and target not in {z['key'] for z in item['completed']}:raise RuntimeError('Required E1 reuse proof missing')
    overlay=Path(smoke_output).resolve()
    if overlay==output or output in overlay.parents or overlay.exists():raise RuntimeError('Smoke requires a NEW sibling evidence directory')
    overlay.mkdir(parents=True);copy_metadata(case,overlay)
    row=next(z for z in rows() if z['case_id']==case_id)
    obj=Smoke(row,overlay,output)
    # Verify and emit every exact completed key before allowing any kernel.
    for z in item['completed']:obj.raw(z['route'],z['config'],z['coordinates'])
    try:obj.run();status='COMPLETE_METADATA'
    except (r.ResourceStop,r.RefinementFailure) as e:status=str(e)
    _,after=inventory(case)
    if before!=after:raise RuntimeError('Production evidence changed during smoke')
    result={'case_id':case_id,'kernel_calls':obj.kernel_calls,'production_files_unchanged':True,
            'status':status,'stats':obj.stats,'smoke_output':str(overlay)}
    s.atomic(overlay/'SMOKE_REPORT.json',result);print(json.dumps(result));return result
