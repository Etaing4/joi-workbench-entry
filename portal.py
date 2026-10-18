#!/usr/bin/env python3
"""GitHub-backed follow-up intake. Uses participant gh authentication, never an owner token."""
import argparse,json,subprocess,sys,hashlib
import entry
REPO='Etaing4/joi-workbench-entry'
MARKER='JOI_PORTAL_V1\n'

from urllib.parse import urlsplit
import ipaddress

def encode(d,artifact_urls=(),qa=False):
 entry.validate(d)
 if len(artifact_urls)>20:raise ValueError('at most 20 artifact URLs')
 for url in artifact_urls:
  u=urlsplit(url)
  if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.hostname in {'localhost','localhost.localdomain'} or u.hostname.endswith(('.local','.internal')):raise ValueError('public HTTPS artifact URL without credentials/query/fragment required')
  try:
   if not ipaddress.ip_address(u.hostname).is_global:raise ValueError('private artifact address')
  except ValueError as e:
   if str(e)=='private artifact address':raise
 raw=MARKER+entry.canonical({'portal_version':1,'submission':d,'artifact_urls':list(artifact_urls),'qa':bool(qa)}).decode()
 if len(raw.encode())>45000:raise ValueError('GitHub snapshot limit 45KB; return larger evidence via artifact URL')
 return raw

def decode(body):
 if not isinstance(body,str) or not body.startswith(MARKER):raise ValueError('not a portal record')
 x=entry.parse_json(body[len(MARKER):].encode())
 if not isinstance(x,dict) or set(x)!={'portal_version','qa','artifact_urls','submission'} or type(x['portal_version']) is not int or x['portal_version']!=1 or type(x['qa']) is not bool or not isinstance(x['artifact_urls'],list) or any(not isinstance(u,str) for u in x['artifact_urls']):raise ValueError('invalid portal envelope')
 encode(x['submission'],x['artifact_urls'],x['qa'])
 return x

def project(issue,comments):
 x=decode(issue['body']);d=x['submission'];receipt=issue['html_url'];rejected=0
 for c in comments:
  if c.get('user',{}).get('login')!=issue['user']['login']:continue
  try:
   candidate=decode(c['body']);new=candidate['submission']
   for k in ['entry_id','cohort','identity','created_at','baseline_ref','label']:
    if new[k]!=d[k]:raise ValueError('immutable field conflict')
   if new['events'][:len(d['events'])]!=d['events'] or len(new['events'])<len(d['events']):raise ValueError('event prefix conflict')
   if len(new['events'])==len(d['events']) and any(new[k]!=d[k] for k in ['tracks','state','limitations']):raise ValueError('append event for revision')
   if candidate.get('qa',False)!=x.get('qa',False):raise ValueError('QA classification immutable')
   d=new;x=candidate;receipt=c['html_url']
  except (ValueError,KeyError,TypeError):rejected+=1
 return {'submission':d,'envelope':x,'rejected_snapshots':rejected,'public':{'entry_id':d['entry_id'],'cohort':{k:d['cohort'][k] for k in ['id','kind','retry_of']},'state':d['state'],'review_state':'pending','tracks':{t:d['tracks'][t]['state'] for t in 'ABCDEFG'},'identity_evidence':'self_reported_unverified','account_authentication':'github_issue_author','receipt_url':receipt,'updated_at':issue['updated_at'],'qa':x.get('qa',False)}}

def api(path,payload=None):
 args=['gh','api',path]
 if payload is not None:args+=['--method','POST','--input','-']
 r=subprocess.run(args,input=json.dumps(payload) if payload is not None else None,capture_output=True,text=True,timeout=60)
 if r.returncode:raise ValueError('GitHub API failed: '+r.stderr[:600])
 return json.loads(r.stdout)

def pages(path):
 rows=[];page=1
 while True:
  batch=api(path+('&' if '?' in path else '?')+'per_page=100&page='+str(page));rows.extend(batch)
  if len(batch)<100:return rows
  page+=1
  if page>100:raise ValueError('pagination safety limit, refusing partial feed')

def publish(path,issue=None,artifact_urls=(),qa=False):
 d=entry.load_bundle(path);body=encode(d,artifact_urls,qa);actor=api('user')['login'];base='repos/'+REPO
 if issue is None:
  target=api(base+'/issues',{'title':'[QA] '+d['entry_id'] if qa else '[Follow-up] '+d['entry_id'],'body':body,'labels':[],'assignees':[]});number=target['number'];read=api(base+'/issues/'+str(number))
 else:
  number=int(issue);old=api(base+'/issues/'+str(number))
  if old['user']['login']!=actor:raise ValueError('only original GitHub author may append progress')
  projected=project(old,pages(base+'/issues/'+str(number)+'/comments'))
  trial={'body':body,'user':{'login':actor},'html_url':'candidate'}
  check=project({'body':encode(projected['submission'],projected['envelope'].get('artifact_urls',[]),qa),'user':{'login':actor},'html_url':'prior','updated_at':old['updated_at']},[trial])
  if check['rejected_snapshots']:raise ValueError('snapshot conflicts with remote entry')
  target=api(base+'/issues/'+str(number)+'/comments',{'body':body});read=api(base+'/issues/comments/'+str(target['id']))
 if read.get('body')!=body or read.get('user',{}).get('login')!=actor:raise ValueError('remote readback mismatch; inspect issue before retry')
 return {'entry_id':d['entry_id'],'issue':number,'receipt_url':read['html_url'],'sha256':entry.digest(body.encode()),'review_state':'pending','identity_authority':'GitHub author authenticated; model/harness self-reported, unverified','assignment_url':'https://etaing4.github.io/joi-workbench-entry/PARTICIPANT.md','cost_usd':None,'qa':qa}

def collect(include_private=False,ledger=None,include_ledger=False):
 ledger={} if ledger is None else ledger;anchor_conflicts=0;observed_issues=set()
 rows=pages('repos/'+REPO+'/issues?state=all&sort=created&direction=asc');out=[];private=[];seen=set();qa=duplicates=invalid=0
 for issue in rows:
  if 'pull_request' in issue:continue
  issue_key=str(issue['number']);observed_issues.add(issue_key)
  if not str(issue.get('body','')).startswith(MARKER):
   if issue_key in ledger:anchor_conflicts+=1
   continue
  comments=pages('repos/'+REPO+'/issues/'+str(issue['number'])+'/comments')
  key=str(issue['number']);observed={'initial_sha256':entry.digest(issue['body'].encode()),'author_sha256':entry.digest(issue['user']['login'].encode()),'comments':{str(c['id']):entry.digest(c['body'].encode()) for c in comments if c.get('user',{}).get('login')==issue['user']['login'] and str(c.get('body','')).startswith(MARKER)}}
  old=ledger.get(key)
  if old and (any(old[k]!=observed[k] for k in ['initial_sha256','author_sha256']) or any(observed['comments'].get(k)!=v for k,v in old['comments'].items())):
   anchor_conflicts+=1;continue
  try:r=project(issue,comments)
  except (ValueError,KeyError,TypeError,RecursionError):invalid+=1;continue
  ledger[key]=observed
  if r['public']['qa']:qa+=1;continue
  eid=r['submission']['entry_id']
  if eid in seen:duplicates+=1;continue
  seen.add(eid);out.append(r['public']);private.append(r)
 result={'schema_version':'joi-public-progress/1','generated_at':entry.now(),'source':'https://github.com/'+REPO+'/issues','cohort_policy':'follow-up only; never frozen baseline','entries':out,'entrant_count':len(out),'qa_count':qa,'duplicate_count':duplicates,'invalid_count':invalid,'identity_policy':'Authenticated GitHub author is not verified model identity; all model and harness observations remain unverified','cost_usd':None}
 anchor_conflicts+=len(set(ledger)-observed_issues)
 result['anchor_conflict_count']=anchor_conflicts
 if include_ledger:result['_ledger']=ledger
 if include_private:result['private_records']=private
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('send');a.add_argument('file');a.add_argument('--issue',type=int);a.add_argument('--artifact-url',action='append',default=[]);a.add_argument('--qa',action='store_true');a.add_argument('--confirm-public',action='store_true',help='confirm benchmark-only metadata and links are public')
 a=s.add_parser('body');a.add_argument('file');a.add_argument('--artifact-url',action='append',default=[]);a.add_argument('--qa',action='store_true')
 args=p.parse_args()
 try:
  if args.command=='body':print(encode(entry.load_bundle(args.file),args.artifact_url,args.qa));return 0
  if not args.confirm_public:raise ValueError('--confirm-public required: issue metadata/artifact URLs will be public')
  print(json.dumps(publish(args.file,args.issue,args.artifact_url,args.qa)));return 0
 except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:print('ERROR: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
