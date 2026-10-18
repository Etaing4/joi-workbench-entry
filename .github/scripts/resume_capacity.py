"""Public-route bounded sustained QA; stdlib only, no owner HTTP credentials."""
import concurrent.futures,hashlib,json,os,secrets,time,urllib.request,urllib.error,threading
BASE='https://shortly-works-resulted-marriage.trycloudflare.com'
REPORT={'qa':True,'host':'GitHub Actions ubuntu-latest','base_url':BASE,'owner_http_credentials':False,'started_at':time.time(),'operations':[],'entries':[]}
LOCK=threading.Lock();sha=lambda b:hashlib.sha256(b).hexdigest()
def req(method,path,body=None,data=None,token=None,headers=None,raw=False):
    payload=json.dumps(body).encode() if body is not None else data
    hdr={'Content-Type':'application/json' if body is not None else 'application/octet-stream',**(headers or {})}
    if token:hdr['Authorization']='Bearer '+token
    start=time.monotonic()
    for attempt in range(20):
        retry_after=0
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(BASE+path,data=payload,method=method,headers=hdr),timeout=90) as r:
                content=r.read();value=content if raw else json.loads(content)
            with LOCK:REPORT['operations'].append({'method':method,'route':path.split('/')[1] if '/' in path else path,'seconds':time.monotonic()-start,'retries':attempt,'request_bytes':len(payload or b'')})
            return value
        except urllib.error.HTTPError as e:
            code=e.code;retry_after=min(30,float(e.headers.get('Retry-After','0')));e.close()
            if code not in (429,502,503,504) or attempt==19:raise RuntimeError('HTTP '+str(code)) from None
        except (TimeoutError,urllib.error.URLError):
            if attempt==19:raise
        time.sleep(max(retry_after,min(10,2*(attempt+1)))+secrets.randbelow(1000)/1000)
RESUME=json.loads(os.environ['JWB_QA_RESUME'])
EXPECTED=json.load(open('.github/fixtures/capacity-expected.json'))['entries']
REPORT['source_workload_run']=39120158278
REPORT['recovery']='same twelve existing QA identities and exact remote chunk bytes; no regenerated payloads or replacement registrations'
def client(item):
    caps={e['attempt_id']:e for e in RESUME};e=caps[item['attempt_id']];t=e['capability_token'];p='/v2/attempts/'+e['attempt_id']
    own=req('GET',p,token=t);assert own['qa'] is True
    candidates=[(uid,u) for uid,u in own.get('uploads',{}).items() if u['path']=='QA/payload.bin' and u['sha256']==item['sha256']]
    assert len(candidates)==1
    uid,u=candidates[0]
    receipt=req('POST',p+'/uploads/'+uid+'/complete',{},token=t);assert receipt['sha256']==item['sha256']
    data=req('GET',p+'/files/QA/payload.bin',token=t,raw=True);assert len(data)==item['bytes'] and sha(data)==item['sha256']
    req('POST',p+'/events',{'kind':'checkpoint','idempotency_key':'checkpoint2','active_seconds':24,'states':{'A':'partial'},'message':'QA complete exact returned bytes'},token=t)
    REPORT['entries'].append({**item,'file_receipt':receipt['receipt'],'exact_recovered_readback':True})
    return e
def phase2(e):
    p='/v2/attempts/'+e['attempt_id'];t=e['capability_token'];data=('post-cold '+e['attempt_id']).encode()
    receipt=req('PUT',p+'/files/QA/postcold.txt',data=data,token=t,headers={'X-Content-SHA256':sha(data),'Idempotency-Key':'postcold-source'})
    assert req('PUT',p+'/files/QA/postcold.txt',data=data,token=t,headers={'X-Content-SHA256':sha(data),'Idempotency-Key':'postcold-source'})==receipt
    assert req('GET',p+'/files/QA/postcold.txt',token=t,raw=True)==data
    req('POST',p+'/events',{'kind':'checkpoint','idempotency_key':'checkpoint3','active_seconds':36,'states':{'A':'partial'},'message':'QA post-cold sustained checkpoint'},token=t)
def wait(e,jid):
    for _ in range(240):
        j=req('GET','/v2/attempts/'+e['attempt_id']+'/jobs/'+jid,token=e['capability_token'])
        if j['state'] in ('finished','failed'):assert j['state']=='finished';return j
        time.sleep(2)
    raise RuntimeError('worker completion timeout')
def main():
    REPORT['initial_health']=req('GET','/health');assert REPORT['initial_health']['store_backend']=='DriveStore'
    assert len(RESUME)==len(EXPECTED)==12
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        entries=list(pool.map(client,EXPECTED));list(pool.map(phase2,entries))
    e=entries[0];p='/v2/attempts/'+e['attempt_id'];t=e['capability_token']
    job=req('POST',p+'/jobs',{'idempotency_key':'code-job','argv':['python','main.py'],'outputs':['answer.txt'],'timeout_seconds':60},token=t)
    j=wait(e,job['job_id']);assert j['result']['runner_receipt']
    assert req('GET',p+'/files/answer.txt',token=t,raw=True)==b'Drive-backed isolated execution'
    REPORT['code_job']={'job_id':job['job_id'],'runner_receipt':j['result']['runner_receipt'],'result_receipt':j['result']['receipt']}
    result=req('POST',p+'/submit',{'idempotency_key':'partial-handin','track_states':{x:'not_attempted' for x in 'ABCDEFGH'},'active_seconds':36,'limitations':['QA excluded; no genuine benchmark result'],'finalized':False},token=t)
    grade=wait(e,result['grade_job_id']);REPORT['submission']=result
    progress=req('GET','/v2/progress');assert not {x['attempt_id'] for x in entries}&{x['attempt_id'] for x in progress['attempts']}
    REPORT['final_health']=req('GET','/health');REPORT['qa_count']=progress['qa_count'];REPORT['genuine_count']=progress['genuine_count']
    REPORT['sustained_pre_and_post_cold_minimum_distinct_entrant_mutations']=120
    REPORT['new_phase2_distinct_mutations']=24
    REPORT['passed']=True;REPORT['finished_at']=time.time()
try:main()
finally:
    with open('capacity-acceptance.json','w') as f:json.dump(REPORT,f,indent=2)
print(json.dumps({'passed':REPORT.get('passed',False),'entries':len(REPORT['entries']),'operations':len(REPORT['operations']),'elapsed_seconds':time.time()-REPORT['started_at']}))
