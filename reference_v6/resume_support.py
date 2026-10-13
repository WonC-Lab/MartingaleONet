"""Infrastructure journals, checked legacy compatibility and single-run lock."""
import contextlib
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

LEGACY_COMMIT='ab9f4fb7c3e2da65471aaf325daa9fb27801bd5c'
LEGACY_EXECUTOR={
    'mp_backend.py':'1acfa66d71f4ac7d28b2c4e6570af2f27a4eef4e28f884d4642e3c71339996a9',
    'run_boundary_certification.py':'3a37abbe4166fb3176feca8f467e1b5ff4d87aa9bb066816b0364dd6e0d6ecb2',
    'requirements-colab.txt':'9084ef2d3dd4e356979c9635fc3ba5059925cd4968afb9d5b1213f57e288ac0b'}


def key(route,cfg,coords):
    # Byte-identical legacy key; never rename or re-key old raw checkpoints.
    return hashlib.sha256(json.dumps([route,cfg,[list(map(str,q)) for q in coords]],sort_keys=True).encode()).hexdigest()


def checked(path):
    z=json.loads(Path(path).read_text(encoding='utf-8'))
    checksum=z.pop('checkpoint_SHA256')
    if hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()!=checksum:
        raise RuntimeError('Checkpoint corrupted: '+str(path))
    return z


def pack(z):
    if isinstance(z,Decimal):return {'_decimal_exact_':str(z)}
    if isinstance(z,dict):return {k:pack(v) for k,v in z.items()}
    if isinstance(z,(list,tuple)):return [pack(v) for v in z]
    return z


def unpack(z):
    if isinstance(z,dict):
        if set(z)=={'_decimal_exact_'}:return Decimal(z['_decimal_exact_'])
        return {k:unpack(v) for k,v in z.items()}
    if isinstance(z,list):return [unpack(v) for v in z]
    return z


def save_journal(path,identity,state):
    z={'journal_schema':1,'identity':identity,'state':pack(state)}
    z['checkpoint_SHA256']=hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
    atomic(path,z)


def load_journal(path,identity):
    if not Path(path).exists():return None
    z=checked(path)
    if z['journal_schema']!=1 or z['identity']!=identity:raise RuntimeError('Journal identity mismatch: '+str(path))
    return unpack(z['state'])


def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    # Unique temp filename prevents accidental shared writer collision. Locks
    # below are the primary protection; this is not a substitute for them.
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temp.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)


def compatible(old,current):
    fields=['protocol_SHA256','input_SHA256','CORE_recomputed','old_boundary_recomputed']
    if any(old.get(k)!=current.get(k) for k in fields):return False
    return old.get('executor_SHA256') in [LEGACY_EXECUTOR,current['executor_SHA256']]


@contextlib.contextmanager
def local_run_lock(output):
    """Kernel lock: same runtime cannot launch two writers on one output tree.

    Drive FUSE locks are not relied on. The notebook also stops its entire OS
    process group when interrupted. A separate Drive lease detects other VMs.
    """
    name=hashlib.sha256(str(Path(output).resolve()).encode()).hexdigest()
    path=Path(tempfile.gettempdir())/('martingale-v6-'+name+'.lock')
    f=path.open('a+b');f.seek(0);f.write(b'0');f.flush();f.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise RuntimeError('Another executor owns this output directory')
        else:
            import fcntl
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Another executor owns this output directory')
        yield
    finally:f.close()


@contextlib.contextmanager
def drive_lease(output,session,takeover=False):
    """Conservative heartbeat guard across VMs; not a distributed atomic lock.

    An active lease blocks execution. A stale lease requires explicit takeover.
    Independent Drive mounts have delayed visibility, so users must not start
    two runtimes simultaneously. Every raw evaluation rechecks its lease owner.
    """
    import threading
    path=Path(output)/'RUNNER_LEASE.json';previous=None
    if path.exists():
        previous=json.loads(path.read_text(encoding='utf-8'))
        if previous.get('active'):
            age=time.time()-previous['heartbeat_epoch']
            if age<180 or not takeover:raise RuntimeError('Existing active/stale Drive lease; stop other runtime first. Stale takeover requires --takeover-stale-lease after 180 seconds.')
    if previous:
        atomic(Path(output)/'sessions'/session/'PREVIOUS_LEASE.json',previous)
    stop=threading.Event();errors=[]
    def refresh(active=True):
        if path.exists():
            owner=json.loads(path.read_text(encoding='utf-8')).get('session_id')
            if owner not in [session,previous.get('session_id') if previous else None]:raise RuntimeError('Drive lease owner changed')
        atomic(path,{'session_id':session,'active':active,'heartbeat_epoch':time.time(),'pid':os.getpid()})
    refresh()
    def pulse():
        while not stop.wait(15):
            try:refresh()
            except Exception as e:errors.append(e);return
    thread=threading.Thread(target=pulse,daemon=True);thread.start()
    try:yield
    finally:
        stop.set();thread.join(timeout=20)
        if not errors:refresh(False)
