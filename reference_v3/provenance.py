"""Verify historical content across Windows/Linux Git text transport."""
import hashlib
import json
from pathlib import Path
from reference_v2.workflow import ROOT

def verified(path,expected):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()==expected:return 'BYTE_IDENTICAL'
    # Git autocrlf may change text transport only. Never accept arbitrary edits.
    if b'\0' not in data:
        lf=data.replace(b'\r\n',b'\n')
        if any(hashlib.sha256(z).hexdigest()==expected for z in [lf,lf.replace(b'\n',b'\r\n')]):return 'EOL_TRANSPORT_ONLY'
    raise RuntimeError('historical content mismatch: '+str(path))

def verify(snapshot):
    return {name:verified(ROOT/name.replace('\\','/'),expected) for name,expected in json.loads(Path(snapshot).read_text()).items()}
