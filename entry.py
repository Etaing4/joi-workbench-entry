#!/usr/bin/env python3
"""Portable Workbench follow-up contract. Python stdlib only; no network by default."""
import argparse, copy, hashlib, json, re, uuid
from datetime import datetime, timezone

BASELINE='JOI-WORKBENCH-20261017-01'
VERSION='joi-portable-entry/1'

def now():
    return datetime.now(timezone.utc).isoformat()

def claim(value, provenance='self_reported'):
    return {'value':value or 'unknown','provenance':provenance}

def register(label, model='unknown', harness='unknown', retry_of=None):
    if retry_of is not None and not re.fullmatch(r'E(?:0[1-9]|10)',retry_of):
        raise ValueError('retry_of must name a frozen baseline route E01–E10')
    return {'schema_version':VERSION,'entry_id':'FU-'+str(uuid.uuid4()),
            'baseline_ref':BASELINE,'cohort':{'id':'FOLLOWUP-'+str(uuid.uuid4()),'kind':'follow-up','retry_of':retry_of},
            'created_at':now(),'label':label,'identity':{'model':claim(model),'harness':claim(harness),'provider':claim('unknown'),'native_session_id':claim('unknown'),'installed_cli':[]},
            'state':'registered','review_state':'pending','tracks':{t:{'state':'not_attempted','summary':'','checks':[],'artifacts':[],'limitations':[]} for t in 'ABCDEFG'},
            'events':[],'artifacts':[],'limitations':[]}

def validate(d):
    if not isinstance(d,dict) or d.get('schema_version')!=VERSION:
        raise ValueError('unsupported schema')
    if d.get('baseline_ref')!=BASELINE or not re.fullmatch(r'FU-[0-9a-f-]{36}',str(d.get('entry_id',''))):
        raise ValueError('follow-up entry only; baseline IDs forbidden')
    c=d.get('cohort',{})
    if c.get('kind')!='follow-up' or not re.fullmatch(r'FOLLOWUP-[0-9a-f-]{36}',str(c.get('id',''))):
        raise ValueError('follow-up cohort required')
    if c.get('retry_of') is not None and not re.fullmatch(r'E(?:0[1-9]|10)',str(c['retry_of'])):
        raise ValueError('invalid retry route')
    if d.get('review_state')!='pending':
        raise ValueError('entrant cannot award review acceptance')
    if set(d.get('tracks',{}))!=set('ABCDEFG'):
        raise ValueError('seven tracks required')
    try:
        if d['state'] not in {'registered','running','blocked','submitted'}:raise ValueError('invalid entry state')
        for k in ['model','harness','provider','native_session_id']:
            x=d['identity'][k]
            if not isinstance(x['value'],str) or len(x['value'])>1000 or x['provenance'] not in {'self_reported','unknown'}:raise ValueError('invalid identity claim')
        for cli in d['identity']['installed_cli']:
            if cli['provenance'] not in {'observed_executable','unknown'}:raise ValueError('invalid CLI provenance')
        if not isinstance(d['label'],str) or len(d['label'])>200:raise ValueError('invalid label')
        for track in d['tracks'].values():
            if track['state'] not in TRACK_STATES or not isinstance(track['summary'],str) or len(track['summary'])>10000:raise ValueError('invalid track')
            for key in ['checks','artifacts','limitations']:
                if not isinstance(track[key],list):raise ValueError('invalid track list')
        if not isinstance(d['events'],list) or len(d['events'])>5000:raise ValueError('event limit')
        for i,event in enumerate(d['events'],1):
            if event['seq']!=i or event['kind'] not in EVENT_KINDS or event['track'] not in [None,*'ABCDEFG'] or event['provenance']!='self_reported':raise ValueError('invalid event')
            if not isinstance(event['message'],str) or len(event['message'])>4000:raise ValueError('invalid event message')
        for a in d['artifacts']:
            safe_name(a['path'])
            if not a['path'].startswith('artifacts/') or not re.fullmatch('[0-9a-f]{64}',a['sha256']) or type(a['bytes']) is not int or not 0<=a['bytes']<=MAX_FILE:raise ValueError('invalid artifact')
        if len(canonical(d))>MAX_JSON:raise ValueError('contract too large')
    except (KeyError,TypeError,AttributeError) as exc:raise ValueError('missing or invalid contract field') from exc
    return d

EVENT_KINDS={'started','checkpoint','blocked','artifact','submitted'}
TRACK_STATES={'not_attempted','running','completed','partial','blocked','failed'}

def append_event(d, kind, track=None, message=''):
    validate(d)
    if kind not in EVENT_KINDS or track not in [None,*'ABCDEFG']:
        raise ValueError('invalid progress event')
    if len(message)>4000: raise ValueError('message too long')
    out=copy.deepcopy(d)
    out['events'].append({'seq':len(out['events'])+1,'at':now(),'kind':kind,'track':track,'message':message,'provenance':'self_reported'})
    out['state']='submitted' if kind=='submitted' else 'blocked' if kind=='blocked' else 'running'
    return out

from pathlib import Path, PurePosixPath
import zipfile, stat
MAX_JSON=2*1024*1024
MAX_FILE=128*1024*1024
MAX_TOTAL=256*1024*1024

def canonical(d):
    return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def digest(b): return hashlib.sha256(b).hexdigest()

def parse_json(raw):
    if len(raw)>MAX_JSON: raise ValueError('JSON too large')
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    def constant(_): raise ValueError('nonfinite number')
    try: return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
    except (RecursionError,UnicodeError,json.JSONDecodeError) as exc: raise ValueError('invalid JSON') from exc

def safe_name(name):
    p=PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or any(x in {'..','.'} for x in name.split('/')) or str(p)!=name:
        raise ValueError('unsafe archive path')
    return name

def export_bundle(d, target, attachments=()):
    validate(d); out=copy.deepcopy(d); files={}; out['artifacts']=[]
    for index,source in enumerate(attachments):
        source=Path(source)
        if source.is_symlink() or not source.is_file() or source.stat().st_size>MAX_FILE:
            raise ValueError('unsafe or oversized artifact')
        name='artifacts/'+str(index)+'-'+re.sub(r'[^a-zA-Z0-9._-]','_',source.name)
        b=source.read_bytes(); files[name]=b
        out['artifacts'].append({'path':name,'sha256':digest(b),'bytes':len(b)})
    files['submission.json']=canonical(out)
    manifest={'schema_version':VERSION,'members':[{'path':n,'sha256':digest(b),'bytes':len(b)} for n,b in sorted(files.items())]}
    if sum(map(len,files.values()))>MAX_TOTAL:raise ValueError('bundle too large')
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_STORED) as z:
        for n,b in sorted(files.items()):z.writestr(n,b)
        z.writestr('manifest.json',canonical(manifest))
    return out

def load_bundle(path):
    path=Path(path)
    if path.stat().st_size>MAX_TOTAL:raise ValueError('bundle too large')
    if path.suffix.lower()!='.zip':
        d=validate(parse_json(path.read_bytes()))
        if d.get('artifacts'): raise ValueError('JSON transport cannot include artifact payloads; use ZIP')
        return d
    with zipfile.ZipFile(path) as z:
        infos=z.infolist(); names=[x.filename for x in infos]
        if len(infos)>200 or len(names)!=len(set(names)) or sum(x.file_size for x in infos)>MAX_TOTAL:raise ValueError('archive limits/duplicate member')
        for i in infos:
            safe_name(i.filename)
            if i.flag_bits&1 or stat.S_ISLNK(i.external_attr>>16) or i.file_size>MAX_FILE or i.is_dir() or i.file_size/max(1,i.compress_size)>200:
                raise ValueError('unsafe archive member')
        if 'manifest.json' not in names or 'submission.json' not in names:raise ValueError('missing manifest/submission')
        m=parse_json(z.read('manifest.json'))
        if m.get('schema_version')!=VERSION:raise ValueError('manifest version')
        members=m.get('members',[])
        if len(members)!=len({x['path'] for x in members}) or {x['path'] for x in members}!=set(names)-{'manifest.json'}:raise ValueError('undeclared member')
        for x in members:
            b=z.read(x['path'])
            if digest(b)!=x['sha256'] or len(b)!=x['bytes']:raise ValueError('digest/size mismatch')
        d=validate(parse_json(z.read('submission.json')))
        if {x['path'] for x in d['artifacts']}!=set(names)-{'manifest.json','submission.json'}:raise ValueError('artifact inventory mismatch')
        for a in d['artifacts']:
            b=z.read(a['path'])
            if not a['path'].startswith('artifacts/') or a['sha256']!=digest(b) or a['bytes']!=len(b):raise ValueError('artifact mismatch')
        return d

def import_bundle(path, inbox):
    """Preserve source bytes and immutable snapshots; never extract or execute attachments."""
    d=load_bundle(path); inbox=Path(inbox); entry=inbox/d['entry_id']; entry.mkdir(parents=True,exist_ok=True)
    raw=Path(path).read_bytes(); h=digest(raw); snapshot=entry/(h+'.json')
    if snapshot.exists():return {'status':'duplicate','review_state':'pending','entry_id':d['entry_id'],'sha256':h}
    for prior in entry.glob('*.json'):
        old=parse_json(prior.read_bytes())
        for k in ['cohort','identity','created_at','baseline_ref','label']:
            if old[k]!=d[k]:raise ValueError('immutable identity/cohort conflict')
        old_events=old['events']; new_events=d['events']
        n=min(len(old_events),len(new_events))
        if old_events[:n]!=new_events[:n]:raise ValueError('event history conflict')
    with snapshot.open('xb') as f:f.write(canonical(d))
    source=entry/(h+('.zip' if Path(path).suffix.lower()=='.zip' else '.source'))
    with source.open('xb') as f:f.write(raw)
    return {'status':'imported','entry_id':d['entry_id'],'sha256':h,'review_state':'pending','identity_authority':'unverified_imported_claims','artifact_execution':'never'}

import shutil, subprocess, sys

def detect_cli(names):
    results=[]
    for name in names:
        if name not in {'python','codex','claude','hermes'}:raise ValueError('unsupported CLI')
        executable=sys.executable if name=='python' else shutil.which(name)
        version='unknown'
        if executable:
            try:
                r=subprocess.run([executable,'--version'],capture_output=True,text=True,timeout=5)
                m=re.search(r'\d+\.\d+(?:\.\d+)?(?:[-a-zA-Z0-9.]*)',r.stdout[:1000])
                if r.returncode==0 and m:version=m.group(0)
            except (OSError,subprocess.TimeoutExpired):pass
        results.append({'name':name,'version':version,'provenance':'observed_executable' if version!='unknown' else 'unknown','scope':'installed executable only; not proof of run/model'})
    return results

def write_json(path,d,exclusive=False):
    with Path(path).open('x' if exclusive else 'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('register'); a.add_argument('--label',required=True); a.add_argument('--model',default='unknown'); a.add_argument('--harness',default='unknown'); a.add_argument('--retry-of'); a.add_argument('--detect',action='append',choices=['python','codex','claude','hermes'],default=[]); a.add_argument('--output',required=True)
    a=s.add_parser('event'); a.add_argument('entry'); a.add_argument('--kind',required=True,choices=sorted(EVENT_KINDS)); a.add_argument('--track',choices=list('ABCDEFG')); a.add_argument('--message',default='')
    a=s.add_parser('track'); a.add_argument('entry'); a.add_argument('track',choices=list('ABCDEFG')); a.add_argument('--state',required=True,choices=sorted(TRACK_STATES)); a.add_argument('--summary',required=True); a.add_argument('--check-command'); a.add_argument('--observed-result'); a.add_argument('--limitation',action='append',default=[])
    a=s.add_parser('export'); a.add_argument('entry'); a.add_argument('--output',required=True); a.add_argument('--artifact',action='append',default=[])
    a=s.add_parser('validate'); a.add_argument('file')
    a=s.add_parser('import'); a.add_argument('file'); a.add_argument('--inbox',required=True)
    a=s.add_parser('adapt'); a.add_argument('file'); a.add_argument('--source',required=True,choices=['cloud-bot','hosted-attachment']); a.add_argument('--output',required=True)
    a=s.add_parser('detect'); a.add_argument('cli',nargs='+',choices=['python','codex','claude','hermes'])
    args=p.parse_args(argv)
    try:
        if args.command=='register':
            d=register(args.label,args.model,args.harness,args.retry_of); d['identity']['installed_cli']=detect_cli(args.detect); write_json(args.output,d,True); result=d
        elif args.command=='detect':result=detect_cli(args.cli)
        elif args.command=='adapt':
            text=Path(args.file).read_bytes()
            if len(text)>MAX_JSON:raise ValueError('attachment too large')
            match=re.fullmatch(rb'\s*[^`]*```(?:json)?\s*\n(.*?)\n```\s*',text,re.S)
            d=validate(parse_json(match.group(1) if match else text)); write_json(args.output,d,True)
            result={'entry_id':d['entry_id'],'adapter':args.source,'source_sha256':digest(text),'identity_authority':'unverified_imported_claims'}
        elif args.command in {'event','track','export'}:
            d=load_bundle(args.entry)
            if args.command=='event':d=append_event(d,args.kind,args.track,args.message); write_json(args.entry,d); result=d
            elif args.command=='track':
                d['tracks'][args.track].update({'state':args.state,'summary':args.summary,'limitations':args.limitation})
                if args.check_command:
                    if args.observed_result is None:raise ValueError('--observed-result required for a check claim')
                    d['tracks'][args.track]['checks'].append({'command':args.check_command,'observed_result':args.observed_result,'provenance':'self_reported'})
                d=append_event(d,'checkpoint',args.track,args.summary); write_json(args.entry,d); result=d
            else:result=export_bundle(d,args.output,args.artifact)
        elif args.command=='import':result=import_bundle(args.file,args.inbox)
        else:result={'valid':True,'entry_id':load_bundle(args.file)['entry_id'],'review_state':'pending'}
        print(json.dumps(result,ensure_ascii=False,allow_nan=False)); return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        print('ERROR: '+str(exc),file=sys.stderr); return 2

if __name__=='__main__':
    raise SystemExit(main())
