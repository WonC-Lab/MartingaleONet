"""Derive resume cursors from old checked raw files. Zero pricing calls.

Creates infrastructure journals/events only. Old scientific reports, raw files,
partials, identities and RESULT.json are not rewritten. Stops at the first raw
evaluation that is not already complete (even when it has partial sums).
"""
import argparse
import json
from pathlib import Path
import time
from unittest.mock import patch
from reference_v6 import run_boundary_certification as runner
from reference_v6 import resume_support as support
from reference_v6.audit_resume import audit


class Missing(Exception):
    def __init__(self,record):self.record=record


class Hydrator(runner.CaseRunner):
    def raw(self,route,cfg,coords):
        k=support.key(route,cfg,coords);path=self.output/'raw'/(k+'.json')
        if not path.exists():
            partial=path.with_suffix('.partial.json')
            state=support.checked(partial) if partial.exists() else None
            raise Missing({'key':k,'route':route,'config':cfg,'coordinates':[list(map(str,q)) for q in coords],
                           'resumed_nodes':state['nodes'] if state else 0})
        return super().raw(route,cfg,coords)

    def publish_history(self,*args):pass


def hydrate(output,audit_dir):
    output=Path(output);audit_dir=Path(audit_dir)
    # Before any journal creation, fully inspect all saved raw/partial files.
    checked=audit(output,audit_dir)
    if not checked['CHECKPOINTS_ACCEPTED']:raise RuntimeError('Audit rejected checkpoints')
    rows={r['case_id']:r for l in (runner.ROOT/'BOUNDARY_BLINDED_INPUTS.jsonl').read_text().splitlines() for r in [json.loads(l,parse_float=str,parse_int=str)]}
    result=[];original_write=runner.write
    def journal_only_write(path,z):
        if Path(path).name in ['COMPONENT_BUDGET_LOCK.json','TIME_REFINEMENT.json'] or Path(path).name.startswith('physical_'):return
        original_write(path,z)
    with support.local_run_lock(output),patch.object(runner,'evaluate',side_effect=AssertionError('Pricing prohibited in hydration')) as blocked,patch.object(runner,'write',side_effect=journal_only_write):
        for case in sorted((output/'cases').iterdir()):
            if not case.is_dir() or case.name not in rows:continue
            rp=case/'RESULT.json';status=json.loads(rp.read_text())['status'] if rp.exists() else 'NO_RESULT'
            if status not in ['PENDING_RESOURCE_LIMIT','NO_RESULT']:
                result.append({'case_id':case.name,'action':'TERMINAL_CASE_SKIPPED','status':status});continue
            obj=Hydrator(rows[case.name],output,time.monotonic()+runner.P['stopping']['batch_wall_seconds'])
            # Full read-only audit already verified these raw bytes. A missing
            # file on a later Drive mount must stop, never silently recompute it.
            snapshot=json.loads((audit_dir/'CHECKPOINT_SNAPSHOT.json').read_text())
            for rel,sha in snapshot.items():
                p=Path(rel)
                if len(p.parts)>=4 and p.parts[1]==case.name and not p.name.endswith('.partial.json'):
                    obj.catalog[p.stem]=sha
            obj.save_catalog()
            try:
                obj.run();item={'case_id':case.name,'action':'ALL_SUBEVALUATIONS_ALREADY_COMPLETE_NO_PRICING'}
            except Missing as e:item={'case_id':case.name,'action':'READY_AT_NEXT_MISSING_SUBEVALUATION','next_missing':e.record}
            except runner.ResourceStop:item={'case_id':case.name,'action':'HYDRATION_RESOURCE_CAP_RESUME_METADATA_ONLY'}
            except runner.RefinementFailure as e:item={'case_id':case.name,'action':'EXISTING_REFINEMENT_CEILING_NO_PRICING','reason':str(e)}
            item['stats']=obj.stats;result.append(item)
            obj.save_catalog()
        assert blocked.call_count==0
    report={'production_pricing_calls':0,'old_scientific_files_overwritten':0,'cases':result}
    support.atomic(audit_dir/'HYDRATION_REPORT.json',report);print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--audit-dir',required=True);a=p.parse_args();hydrate(a.output,a.audit_dir)
