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
    for attempt in range(4):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(BASE+path,data=payload,method=method,headers=hdr),timeout=90) as r:
                content=r.read();value=content if raw else json.loads(content)
            with LOCK:REPORT['operations'].append({'method':method,'route':path.split('/')[2] if '/' in path else path,'seconds':time.monotonic()-start,'retries':attempt,'request_bytes':len(payload or b'')})
            return value
        except urllib.error.HTTPError as e:
            code=e.code;e.close()
            if code not in (429,502,503,504) or attempt==3:raise RuntimeError('HTTP '+str(code)) from None
        except (TimeoutError,urllib.error.URLError):
            if attempt==3:raise
        time.sleep(2*(attempt+1))
def register(i):
    body={'label':'QA capacity recovery '+str(i),'identity':{'model':'QA-not-an-entrant','harness':'external stdlib'},'qa':True,'idempotency_key':secrets.token_hex(32)}
    e=req('POST','/v2/attempts',body);assert req('POST','/v2/attempts',body)==e
    e['path']='/v2/attempts/'+e['attempt_id'];e['data']=os.urandom(8*1024**2+17);e['sha256']=sha(e['data'])
    REPORT['entries'].append({'attempt_id':e['attempt_id'],'registration_receipt':BASE+e['receipt_url'],'sha256':e['sha256'],'bytes':len(e['data'])})
    return e
def stage(e):
    p=e['path'];token=e['capability_token'];code=b'from pathlib import Path\nPath("answer.txt").write_text("Drive-backed isolated execution")\n'
    r=req('PUT',p+'/files/main.py',data=code,token=token,headers={'X-Content-SHA256':sha(code),'Idempotency-Key':'source'})
    assert req('GET',p+'/files/main.py',token=token,raw=True)==code
    e['upload']=req('POST',p+'/uploads',{'path':'QA/payload.bin','size':len(e['data']),'sha256':e['sha256'],'idempotency_key':'large-upload'},token=token)['upload_id']
    req('POST',p+'/events',{'kind':'checkpoint','idempotency_key':'checkpoint1','active_seconds':12,'states':{'A':'partial'},'message':'QA staged; not genuine work'},token=token)
def chunk(e,i):
    part=e['data'][i*4194304:(i+1)*4194304];p=e['path']+'/uploads/'+e['upload'];hdr={'X-Content-SHA256':sha(part)}
    r=req('PUT',p+'/chunks/'+str(i),data=part,token=e['capability_token'],headers=hdr)
    if i==0:
        assert req('PUT',p+'/chunks/0',data=part,token=e['capability_token'],headers=hdr)==r
        assert 0 in req('GET',p,token=e['capability_token'])['received_chunks']
def complete(e):
    p=e['path'];t=e['capability_token']
    r=req('POST',p+'/uploads/'+e['upload']+'/complete',{},token=t);assert r['sha256']==e['sha256']
    assert sha(req('GET',p+'/files/QA/payload.bin',token=t,raw=True))==e['sha256']
    req('POST',p+'/events',{'kind':'checkpoint','idempotency_key':'checkpoint2','active_seconds':24,'states':{'A':'partial'},'message':'QA complete exact returned bytes'},token=t)
def wait(e,jid):
    for _ in range(180):
        j=req('GET',e['path']+'/jobs/'+jid,token=e['capability_token'])
        if j['state'] in ('finished','failed'):assert j['state']=='finished';return j
        time.sleep(2)
    raise RuntimeError('worker completion timeout')
def main():
    REPORT['initial_health']=req('GET','/health');assert REPORT['initial_health']['store_backend']=='DriveStore'
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        entries=list(pool.map(register,range(12)));assert len({e['attempt_id'] for e in entries})==12
        list(pool.map(stage,entries))
        for i in range(3):list(pool.map(lambda e:chunk(e,i),entries))
        list(pool.map(complete,entries))
    e=entries[0];job=req('POST',e['path']+'/jobs',{'idempotency_key':'code-job','argv':['python','main.py'],'outputs':['answer.txt'],'timeout_seconds':60},token=e['capability_token'])
    j=wait(e,job['job_id']);assert j['result']['runner_receipt'];assert req('GET',e['path']+'/files/answer.txt',token=e['capability_token'],raw=True)==b'Drive-backed isolated execution'
    REPORT['code_job']={'job_id':job['job_id'],'result_receipt':j['result']['receipt']}
    result=req('POST',e['path']+'/submit',{'idempotency_key':'partial-handin','track_states':{t:'not_attempted' for t in 'ABCDEFGH'},'active_seconds':24,'limitations':['QA excluded; no genuine benchmark result'],'finalized':False},token=e['capability_token'])
    wait(e,result['grade_job_id']);REPORT['submission']=result
    progress=req('GET','/v2/progress');assert not {e['attempt_id'] for e in entries}&{r['attempt_id'] for r in progress['attempts']}
    REPORT['final_health']=req('GET','/health');REPORT['genuine_count']=progress['genuine_count'];REPORT['qa_count']=progress['qa_count']
    REPORT['passed']=True;REPORT['finished_at']=time.time();REPORT['entrant_mutations_minimum']=108
try:main()
finally:
    with open('capacity-acceptance.json','w') as f:json.dump(REPORT,f,indent=2)
print(json.dumps({'passed':REPORT.get('passed',False),'entries':len(REPORT['entries']),'operations':len(REPORT['operations']),'elapsed_seconds':time.time()-REPORT['started_at']}))
