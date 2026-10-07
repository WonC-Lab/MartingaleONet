"""Immutable local CORE transport: no pricing call or automatic full sweep."""
import argparse,gzip,hashlib,json,io,zipfile
from pathlib import Path
from reference.certify import dump
from reference_v2.workflow import ROOT
from reference_v2.domains import all_core
from .coverage import key

SOURCES=['reference/route_a.py','reference/route_b.py','reference/certify.py','reference/types.py','reference/derivatives.py','reference/certification_grid.py','reference_v2/domains.py']
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(path):return sha(path.read_bytes().replace(b'\r\n',b'\n'))

def validate(data):
    rows=[json.loads(z) for z in data.decode('utf-8').splitlines()]
    expected={key(c.row()) for c in all_core()};actual={key(r) for r in rows}
    if len(rows)!=1734 or len(actual)!=1734 or actual!=expected:raise RuntimeError('immutable CORE must contain exactly the original 1734 inputs')
    if any(r.get('status') not in ['PASS','FAIL'] for r in rows):raise RuntimeError('missing original final row status')
    return rows

def pack():
    source=ROOT/'reference_v3/coverage_core.jsonl';data=source.read_bytes();rows=validate(data)
    folder=ROOT/'reference_v3/immutable';folder.mkdir(exist_ok=True)
    archive=folder/'local_core_1734.jsonl.gz';manifest=folder/'LOCAL_CORE_MANIFEST.json'
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        if previous['uncompressed_sha256']!=sha(data):raise RuntimeError('completed immutable CORE changed')
        if sha(archive.read_bytes())!=previous['archive_sha256']:raise RuntimeError('immutable archive changed')
        return
    archive.write_bytes(gzip.compress(data,compresslevel=9,mtime=0))
    dump(manifest,dict(planned=1734,evaluated=1734,source='reference_v3/coverage_core.jsonl',uncompressed_sha256=sha(data),archive_sha256=sha(archive.read_bytes()),source_canonical_sha256={p:canonical(ROOT/p) for p in SOURCES},original_strict_PASS=sum(r['status']=='PASS' for r in rows),original_strict_FAIL=sum(r['status']=='FAIL' for r in rows),reuse_policy='Verify bytes, catalog and engine content; import without assessing or repricing any CORE input. Missing/mismatched baseline aborts, never triggers a full sweep.'))

def import_core(output):
    folder=ROOT/'reference_v3/immutable';m=json.loads((folder/'LOCAL_CORE_MANIFEST.json').read_text());archive=folder/'local_core_1734.jsonl.gz'
    if sha(archive.read_bytes())!=m['archive_sha256']:raise RuntimeError('CORE archive SHA mismatch')
    data=gzip.decompress(archive.read_bytes())
    if sha(data)!=m['uncompressed_sha256']:raise RuntimeError('CORE raw SHA mismatch')
    for p,h in m['source_canonical_sha256'].items():
        if canonical(ROOT/p)!=h:raise RuntimeError('pricing source changed: '+p)
    validate(data)
    root=Path(output);root.mkdir(parents=True,exist_ok=True);target=root/'coverage_core.jsonl'
    if target.exists():
        if target.read_bytes()!=data:raise RuntimeError('existing output CORE differs; refusing overwrite')
    else:target.write_bytes(data)
    dump(root/'CORE_REUSE_RECEIPT.json',dict(reused=1734,recomputed=0,source_manifest='reference_v3/immutable/LOCAL_CORE_MANIFEST.json',verified_uncompressed_sha256=m['uncompressed_sha256'],deliberate_environment_cross_validation_subset=[],pricing_calls_in_import=0))
    print('Immutable CORE verified and reused: 1734; recomputed: 0',flush=True)

def import_evidence(output):
    root=Path(output)
    manifests=sorted(p for p in (ROOT/'reference_v3/immutable').glob('LOCAL_EVIDENCE_MANIFEST*.json') if not p.stem.endswith('_BUNDLE'))
    manifest_path=manifests[-1] if manifests else None
    manifest=json.loads(manifest_path.read_text()) if manifest_path else None
    if manifest is None:raise RuntimeError('missing saved local evidence manifest; publish the completed checkpoint snapshot first')
    # A fresh clone may omit loose checkpoint files. The immutable bundle
    # transports every manifest entry; validate everything before any writes.
    bundle=manifest_path.with_suffix('.zip')
    metadata=manifest_path.with_name(manifest_path.stem+'_BUNDLE.json')
    payloads={}
    if bundle.exists():
        if not metadata.exists():raise RuntimeError('missing evidence bundle checksum: '+str(metadata))
        record=json.loads(metadata.read_text())
        if sha(bundle.read_bytes())!=record['archive_sha256']:raise RuntimeError('evidence bundle SHA mismatch')
        from .provenance import verified
        verified(manifest_path,record['manifest_sha256'])
        with zipfile.ZipFile(bundle) as archive:
            if set(archive.namelist())!=set(manifest['files']):raise RuntimeError('evidence bundle catalog mismatch')
            payloads={name:archive.read(name) for name in manifest['files']}
    else:
        missing=[name for name in manifest['files'] if not (ROOT/name).is_file()]
        if missing:raise RuntimeError('local evidence files missing from clone: '+str(len(missing))+'; publish '+str(bundle.relative_to(ROOT))+' and its _BUNDLE.json checksum. First missing: '+missing[0]+'. CORE remains reused; no full sweep is triggered.')
        payloads={name:(ROOT/name).read_bytes() for name in manifest['files']}
    for name,expected in manifest['files'].items():
        data=payloads[name]
        variants=[data,data.replace(b'\r\n',b'\n'),data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')]
        if not any(sha(v)==expected for v in variants):raise RuntimeError('evidence SHA mismatch: '+name)
        relative=Path(name).relative_to('reference_v3')
        if '..' in relative.parts or (relative.parts[0] not in ['mp_cases','external_checkpoints'] and str(relative)!='boundary_required.jsonl'):raise RuntimeError('invalid evidence path: '+name)
        target=root/relative
        if target.exists() and str(relative)!='boundary_required.jsonl':
            if target.read_bytes() not in variants:raise RuntimeError('checkpoint differs: '+str(target))
    for name,data in payloads.items():
        target=root/Path(name).relative_to('reference_v3')
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    dump(root/'EVIDENCE_REUSE_RECEIPT.json',dict(source_manifest=str(manifest_path.relative_to(ROOT)),transport='immutable_zip' if bundle.exists() else 'loose_files',verified_files=len(payloads),pricing_calls_in_import=0))
    print('Existing numerical checkpoints imported; no pricing calls',flush=True)

def pack_evidence():
    root=ROOT/'reference_v3';files=[p for folder in ['mp_cases','external_checkpoints'] for p in (root/folder).rglob('*.json')]
    files += [p for p in [root/'boundary_required.jsonl'] if p.exists()]
    manifests=sorted(p for p in (root/'immutable').glob('LOCAL_EVIDENCE_MANIFEST*.json') if not p.stem.endswith('_BUNDLE'))
    manifest=manifests[-1] if manifests else root/'immutable/LOCAL_EVIDENCE_MANIFEST.json'
    record=dict(files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in files},note='Completed local point/setting evidence only; CORE is separately frozen. No missing point is represented as passed.')
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        if previous==record:return
        if any(record['files'].get(k)!=v for k,v in previous['files'].items()):raise RuntimeError('frozen local evidence changed; do not overwrite')
        manifest=root/'immutable'/('LOCAL_EVIDENCE_MANIFEST_'+str(len(manifests)).zfill(4)+'.json')
        dump(manifest,record)
    else:dump(manifest,record)

def pack_evidence_bundle():
    manifest=sorted(p for p in (ROOT/'reference_v3/immutable').glob('LOCAL_EVIDENCE_MANIFEST*.json') if not p.stem.endswith('_BUNDLE'))[-1]
    # Bundle metadata is intentionally excluded from manifest discovery.
    record=json.loads(manifest.read_text())
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,expected in sorted(record['files'].items()):
            data=(ROOT/name).read_bytes()
            if sha(data)!=expected:raise RuntimeError('frozen local evidence changed: '+name)
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    data=buffer.getvalue();bundle=manifest.with_suffix('.zip')
    metadata=manifest.with_name(manifest.stem+'_BUNDLE.json')
    expected=dict(archive_sha256=sha(data),manifest_sha256=sha(manifest.read_bytes()),files=len(record['files']))
    if bundle.exists() and bundle.read_bytes()!=data:raise RuntimeError('immutable evidence bundle differs; refusing overwrite')
    if metadata.exists() and json.loads(metadata.read_text())!=expected:raise RuntimeError('immutable bundle metadata differs')
    if not bundle.exists():bundle.write_bytes(data)
    if not metadata.exists():dump(metadata,expected)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pack','import']);p.add_argument('--output',default='reference_v3_colab');a=p.parse_args()
    if a.action=='pack':pack();pack_evidence();pack_evidence_bundle()
    else:import_core(a.output);import_evidence(a.output)
