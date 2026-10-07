"""Training-support v->0+ sequences; no evaluation-only OOD expansion."""
import argparse,hashlib,json
from pathlib import Path
from reference.types import Case
from reference.certification_grid import REGIMES
from reference_v2.domains import parameter_core
from reference_v2.high_precision import MPConfig,serial
from reference_v2.workflow import span
from reference.certify import dump
from .mp import Integrator
from .coverage import key

def run(output='reference_v3'):
    root=Path(output);folder=root/'continuity_checkpoints';folder.mkdir(exist_ok=True);by={}
    for p in (root/'mp_cases').rglob('*.json'):
        z=json.loads(p.read_text());by[key(z['input'])]=z
    for i,p in enumerate(REGIMES):
        if not parameter_core(p):continue
        for tau in [1/252,.1,1.]:
            c=Case(0,0,tau,1,p,'continuity_R'+str(i));target=folder/(hashlib.sha256(json.dumps(key(c.row())).encode()).hexdigest()[:20]+'.json')
            if target.exists():continue
            evidence=by.get(key(c.row()),{});cut=evidence.get('cutoff',[{'config':{'cutoff':32768}}])[-1]['config']['cutoff'];obj=Integrator(c,MPConfig(80,cut,40,span(c)));rows=[]
            for v in ['0','1e-8','1e-7','1e-6','1e-5','1e-4','1e-3','1e-2']:
                rows.append(dict(v=v,values=serial(obj.ctx,obj.values(v=obj.ctx.mpf(v)))))
            dump(target,dict(input=c.row(),config=obj.cfg.__dict__,rows=rows,status='DIAGNOSTIC',v0_point_status=evidence.get('status','UNRESOLVED'),training_required_compatibility=True));print('continuity',c.label,tau,flush=True)
    dump(root/'BOUNDARY_CONTINUITY.json',dict(rows=[json.loads(p.read_text()) for p in folder.glob('*.json')],planned_sequences=15,planned_values=120))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');run(p.parse_args().output)
