"""Build bounded Drive-read evidence tables; never price a production input."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import time
from unittest.mock import patch
from reference_v6 import resume_support as support
from reference_v6 import run_boundary_certification as runner

ROOT=Path(__file__).resolve().parent
evidence=ROOT/'evidence'
metadata=json.loads((evidence/'DRIVE_METADATA.json').read_text(encoding='utf-8'))
rows={r['case_id']:r for line in (runner.ROOT/'BOUNDARY_BLINDED_INPUTS.jsonl').read_text().splitlines() for r in [json.loads(line,parse_float=str,parse_int=str)]}
log=(evidence/'EXECUTION.log.txt').read_text(encoding='utf-8')
sessions=log.split('COMMAND:')
pattern=re.compile(r'^(v6_\d+_\d+) (E[12]) raw checkpoint saved: (\{.*\}), (\d+) nodes, ([\d.]+)s$',re.M)
summaries={};records=[];partials=[]
for case in ['v6_01_0','v6_01_1','v6_01_2']:
    result=json.loads((evidence/case/'RESULT.json').read_text())
    session_records=[]
    for i,session in enumerate(sessions):
        matches=[m for m in pattern.findall(session) if m[0]==case]
        if matches:
            session_records.append({'log_session':i,'newly_saved_config_lines':len(matches),'recorded_wall_seconds':round(sum(float(m[4]) for m in matches),1),
                                    'first_config':ast.literal_eval(matches[0][2]),'last_config':ast.literal_eval(matches[-1][2])})
    summaries[case]={'last_status':result['status'],'last_attempt_stats':result.get('stats',{}),
                     'log_sessions':session_records,'exact_recomputation_proven':False,'wasted_production_seconds':None,
                     'limitation':'Old log lacks coordinates/key and cache-hit events; equal config can be a different stencil. Metadata inventory limited to newest100 per folder.'}
    lookup={m['name']:m for m in metadata[case]}
    for path in (evidence/case).glob('*.json'):
        if len(path.name.split('.')[0])!=64:continue
        z=support.checked(path)
        if path.name.endswith('.partial.json'):
            assert isinstance(z['nodes'],int) and z['nodes']>=0
            assert all(len(q)==3 and all(len(t)==4 and all(isinstance(i,int) for i in t) for t in q) for q in z['sums']+z['absolute'])
            partials.append({'case_id':case,'key':path.name.split('.')[0],'nodes':z['nodes'],'validation':'LEGACY_CHECKSUM_AND_MP_TUPLE_LAYOUT_VALID'})
            continue
        assert support.key(z['route'],z['config'],z['coordinates'])==path.stem
        records.append({'case_id':case,'key':path.stem,'route':z['route'],'config':z['config'],'coordinates':z['coordinates'],
                        'created':lookup[path.name]['created'],'modified':lookup[path.name]['modified'],
                        'recorded_elapsed_seconds':z['elapsed_seconds'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'action_in_controlled_loading_test':'REUSED','action_in_old_session':'NOT_OBSERVABLE_FROM_KEYLESS_LOG'})
with tempfile.TemporaryDirectory() as td:
    for record in records:
        case=record['case_id'];source=evidence/case/(record['key']+'.json')
        target=Path(td)/'cases'/case/'raw'/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    with patch.object(runner,'evaluate',side_effect=AssertionError('Production pricing forbidden during audit')) as blocked:
        for record in records:
            obj=runner.CaseRunner(rows[record['case_id']],td,time.monotonic()+300)
            obj.raw(record['route'],record['config'],record['coordinates'])
            assert obj.stats=={'cached_evaluations':1,'new_evaluations':0}
        assert blocked.call_count==0
proof={'production_pricing_calls':0,'completed_exact_evaluations_loaded_without_backend':len(records),
       'legacy_partials_checked_without_execution':len(partials),'legacy_identity':json.loads((evidence/'RUN_IDENTITY.json').read_text()),
       'current_legacy_environment':json.loads((evidence/'ENVIRONMENT.json').read_text()),'cases':summaries,
       'prior_identity_revision_read':'Drive connector lists revisions but cannot fetch JSON revision content; prior hashes/commits not independently read back.',
       'five_preflight_and_execution_commands':'All recorded output directories match /content/drive/MyDrive/MartingaleONet/reference_v6_colab; current identity and commit match ab9f4fb.'}
(ROOT/'OBSERVED_PRODUCTION_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
(ROOT/'VERIFIED_SUBEVALUATIONS.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
(ROOT/'VERIFIED_PARTIALS.json').write_text(json.dumps(partials,indent=2)+'\n',encoding='utf-8')
with (ROOT/'VERIFIED_SUBEVALUATIONS.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
with (ROOT/'LEGACY_NEW_SESSION_CONFIGS.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['log_session','case_id','route','config','nodes','elapsed_seconds','exact_duplicate_classification'])
    for i,session in enumerate(sessions):
        for m in pattern.findall(session):
            if m[0] in summaries:w.writerow([i,*m,'UNDETERMINED_COORDINATES_NOT_LOGGED'])
print(json.dumps({'completed_exact_checkpoints_reused':len(records),'partials_validated':len(partials),'production_pricing_calls':0,'case_summary':summaries},indent=2))
