"""Read-only production checkpoint audit. Never imports/calls a pricing worker."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import ast
from reference_v6 import resume_support as support


def audit(output,audit_dir,prior=None):
    output=Path(output).resolve();audit_dir=Path(audit_dir).resolve()
    if audit_dir==output or output in audit_dir.parents:raise ValueError('Audit output must be outside the production directory')
    identity=json.loads((output/'RUN_IDENTITY.json').read_text(encoding='utf-8'))
    root=Path(__file__).resolve().parent
    protocol=hashlib.sha256((root/'BOUNDARY_CERT_PROTOCOL.json').read_bytes()).hexdigest()
    inputs=hashlib.sha256((root/'BOUNDARY_BLINDED_INPUTS.jsonl').read_bytes()).hexdigest()
    from reference_v6.run_boundary_certification import fingerprint
    current={'protocol_SHA256':protocol,'input_SHA256':inputs,'executor_SHA256':fingerprint(),
             'CORE_recomputed':0,'old_boundary_recomputed':0}
    snapshot={};entries=[];errors=[];statuses={}
    for case in sorted((output/'cases').glob('*')):
        if not case.is_dir():continue
        rp=case/'RESULT.json'
        statuses[case.name]=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {'status':'NO_RESULT'}
        for path in sorted((case/'raw').glob('*.json')):
            rel=str(path.relative_to(output));sha=hashlib.sha256(path.read_bytes()).hexdigest();snapshot[rel]=sha
            try:
                z=support.checked(path);partial=path.name.endswith('.partial.json')
                if partial:
                    if not isinstance(z['nodes'],int) or z['nodes']<0:raise RuntimeError('invalid node position')
                    for name in ['sums','absolute']:
                        if not isinstance(z[name],list):raise RuntimeError('invalid accumulator')
                        for q in z[name]:
                            if len(q)!=3 or any(len(t)!=4 or any(not isinstance(n,int) for n in t) for t in q):raise RuntimeError('invalid MP tuple')
                    entry={'case_id':case.name,'path':rel,'key':path.name.split('.')[0],'kind':'PARTIAL',
                           'nodes':z['nodes'],'validation':'CHECKSUM_AND_LAYOUT_VALID','sha256':sha}
                else:
                    expected=support.key(z['route'],z['config'],z['coordinates'])
                    if path.stem!=expected:raise RuntimeError('legacy raw key mismatch')
                    entry={'case_id':case.name,'path':rel,'key':expected,'kind':'COMPLETED',
                           'route':z['route'],'config':z['config'],'coordinates':z['coordinates'],
                           'nodes':z['nodes'],'elapsed_seconds':z.get('elapsed_seconds'),'sha256':sha,'validation':'CHECKSUM_AND_KEY_VALID'}
                entries.append(entry)
            except Exception as e:errors.append({'path':rel,'error':str(e)})
    old=json.loads(Path(prior).read_text(encoding='utf-8')) if prior else None
    for e in entries:
        e['inventory_comparison']=('UNCHANGED_REUSED_FILE' if old and old.get(e['path'])==e['sha256'] else
                                   'CHANGED_OR_RECOMPUTED_FILE' if old and e['path'] in old else
                                   'NEW_FILE' if old else 'NO_PRIOR_BYTE_SNAPSHOT')
    events=[]
    for p in sorted((output/'cases').glob('*/events/*.jsonl')):
        for line in p.read_text(encoding='utf-8').splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:errors.append({'path':str(p),'error':'truncated event line'})
    audit_dir.mkdir(parents=True,exist_ok=True)
    support.atomic(audit_dir/'CHECKPOINT_SNAPSHOT.json',snapshot)
    support.atomic(audit_dir/'SUBEVALUATIONS.json',entries)
    support.atomic(audit_dir/'EVENTS.json',events)
    previously_completed={(Path(k).parts[1],Path(k).stem) for k in (old or {}) if not k.endswith('.partial.json') and len(Path(k).parts)>=4}
    comparison=[];wasted_wall=0;wasted_cpu=0
    for e in sorted(events,key=lambda z:(z.get('UTC',''),z.get('session_id',''))):
        action=e['action'];k=(e['case_id'],e.get('key'));duplicate=False
        if action=='COMPLETED':
            duplicate=k in previously_completed
            if duplicate:
                wasted_wall+=e.get('elapsed_seconds',0);wasted_cpu+=e.get('backend_CPU_seconds',0)
            previously_completed.add(k)
        comparison.append({**e,'classification':'RECOMPUTED' if duplicate else action})
    support.atomic(audit_dir/'EXECUTION_COMPARISON.json',comparison)
    with (audit_dir/'SUBEVALUATIONS.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['case_id','key','kind','route','config','coordinates','nodes','elapsed_seconds','validation','inventory_comparison']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(entries)
    bycase={}
    for name,z in statuses.items():
        subset=[e for e in entries if e['case_id']==name]
        bycase[name]={'status':z['status'],'last_attempt_stats':z.get('stats',{}),
                      'completed_E1':sum(e.get('route')=='E1' for e in subset),'completed_E2':sum(e.get('route')=='E2' for e in subset),
                      'partials':sum(e['kind']=='PARTIAL' for e in subset),
                      'journals':len(list((output/'cases'/name/'resume').glob('*.json')))}
    summary={'production_directory':str(output),'stored_identity':identity,'current_identity':current,
             'accepted_legacy_or_current_identity':support.compatible(identity,current),'case_inventory':bycase,
             'errors':errors,'CHECKPOINTS_ACCEPTED':support.compatible(identity,current) and not errors and bool(entries),
             'production_pricing_calls':0,'production_files_modified':0,
             'event_proven_duplicate_wall_seconds':wasted_wall,'event_proven_duplicate_CPU_seconds':wasted_cpu,
             'event_proof_scope':'Patched keyed events only; zero does not establish zero waste in old keyless logs.',
             'legacy_log_limit':'Old log omits key/coordinates and REUSED events; equal config alone is not proof of duplicate computation.',
             'wasted_time':'Exact key-based duplicate timing requires events or prior byte snapshot; never infer it from repeated cutoff labels.'}
    support.atomic(audit_dir/'AUDIT_SUMMARY.json',summary)
    print(json.dumps(summary,indent=2),flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--audit-dir',required=True);p.add_argument('--prior-snapshot')
    args=p.parse_args();s=audit(args.output,args.audit_dir,args.prior_snapshot)
    if not s['CHECKPOINTS_ACCEPTED']:raise SystemExit('Audit rejected checkpoints; do not run production')


if __name__=='__main__':main()
