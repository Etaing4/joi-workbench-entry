"""Owned QA only: account-neutral public client; never log capabilities."""
import concurrent.futures, hashlib, json, os, secrets, time, urllib.request, urllib.error
BASE='https://shortly-works-resulted-marriage.trycloudflare.com'
sha=lambda b:hashlib.sha256(b).hexdigest()
REPORT={'qa':True,'execution_host':'GitHub Actions ubuntu-latest','started_at':time.time(),'base_url':BASE,'owner_credentials_used_by_http_client':False,'checks':{}}
def req(method,path,body=None,data=None,token=None,headers=None,raw=False):
    payload=json.dumps(body).encode() if body is not None else data
    hdr={'Content-Type':'application/json' if body is not None else 'application/octet-stream',**(headers or {})}
    if token:hdr['Authorization']='Bearer '+token
    for n in range(4):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(BASE+path,data=payload,method=method,headers=hdr),timeout=240) as r:
                b=r.read();return (b,dict(r.headers)) if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            code=e.code;e.close()
            if code not in (429,502,503,504) or n==3:raise RuntimeError('public HTTP '+str(code)) from None
        except (TimeoutError,urllib.error.URLError):
            if n==3:raise
        time.sleep(2*(n+1))
def register(i):
    body={'label':'QA public acceptance '+str(i),'identity':{'model':'not-a-genuine-entrant','provider':'QA','harness':'GitHub Actions stdlib'},'idempotency_key':secrets.token_hex(32),'qa':True}
    r=req('POST','/v2/attempts',body);assert req('POST','/v2/attempts',body)==r
    assert req('GET',r['receipt_url'])['attempt_id']==r['attempt_id']
    return r
def wait_job(entry,jid):
    for _ in range(240):
        j=req('GET','/v2/attempts/'+entry['attempt_id']+'/jobs/'+jid,token=entry['capability_token'])
        if j['state'] in ('finished','failed'):assert j['state']=='finished',j.get('result',{}).get('failure');return j
        time.sleep(3)
    raise RuntimeError('job wait expired')
def main():
    REPORT['health']=req('GET','/health')
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:entries=list(pool.map(register,range(12)))
    assert len({e['attempt_id'] for e in entries})==12
    REPORT['registration_receipts']=[{'attempt_id':e['attempt_id'],'receipt_url':BASE+e['receipt_url']} for e in entries]
    REPORT['checks']['12_concurrent_idempotent_registrations']=True
    e=entries[0];t=e['capability_token'];p='/v2/attempts/'+e['attempt_id']
    code=b"from pathlib import Path\nPath('answer.txt').write_text('QA public isolated execution')\nprint('QA execution, not benchmark acceptance')\n"
    r=req('PUT',p+'/files/main.py',data=code,token=t,headers={'X-Content-SHA256':sha(code),'Idempotency-Key':'qa-source'})
    assert req('PUT',p+'/files/main.py',data=code,token=t,headers={'X-Content-SHA256':sha(code),'Idempotency-Key':'qa-source'})==r
    assert req('GET',p+'/files/main.py',token=t,raw=True)[0]==code
    try:req('GET',p+'/files/main.py',token=entries[1]['capability_token']);raise AssertionError('cross capability allowed')
    except RuntimeError as ex:assert str(ex)=='public HTTP 404'
    REPORT['checks']['immutable_code_exact_readback_cross_denial']=True
    job=req('POST',p+'/jobs',{'idempotency_key':'qa-code','argv':['python','main.py'],'timeout_seconds':60,'outputs':['answer.txt']},token=t)
    j=wait_job(e,job['job_id']);assert j['result']['runner_receipt']
    REPORT['code_job']={'job_id':j['job_id'],'runner_receipt':j['result']['runner_receipt'],'receipt':j['result']['receipt']}
    film_job=req('POST',p+'/jobs',{'idempotency_key':'qa-real-media','argv':['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=1280x720:rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','10','-c:v','libx264','-preset','ultrafast','-b:v','16M','-minrate','16M','-maxrate','16M','-bufsize','32M','-c:a','aac','-movflags','+faststart','qa.mp4'],'timeout_seconds':120,'outputs':['qa.mp4']},token=t)
    j=wait_job(e,film_job['job_id']);film,hdr=req('GET',p+'/files/qa.mp4',token=t,raw=True);digest=sha(film)
    assert len(film)>8388608 and digest==j['result']['outputs'][0]['sha256']
    u=req('POST',p+'/uploads',{'path':'QA/returned.mp4','size':len(film),'sha256':digest,'idempotency_key':'qa-media-upload'},token=t);up=p+'/uploads/'+u['upload_id']
    for i,offset in enumerate(range(0,len(film),u['chunk_size'])):
        part=film[offset:offset+u['chunk_size']];r=req('PUT',up+'/chunks/'+str(i),data=part,token=t,headers={'X-Content-SHA256':sha(part)})
        if i==0:
            assert req('PUT',up+'/chunks/0',data=part,token=t,headers={'X-Content-SHA256':sha(part)})==r
            assert 0 in req('GET',up,token=t)['received_chunks']
    r=req('POST',up+'/complete',{},token=t);assert r['sha256']==digest
    assert req('GET',p+'/files/QA/returned.mp4',token=t,raw=True)[0]==film
    REPORT['media']={'job_id':j['job_id'],'bytes':len(film),'sha256':digest,'receipt':r['receipt'],'runner_receipt':j['result']['runner_receipt'],'classification':'QA synthetic tool/transport qualification, not G/H film'}
    submit=req('POST',p+'/submit',{'idempotency_key':'qa-submit','track_states':{x:'not_attempted' for x in 'ABCDEFGH'},'active_seconds':0,'limitations':['QA only; synthetic media; excluded from genuine findings'],'finalized':True,'publish_review':True},token=t)
    grade=wait_job(e,submit['grade_job_id']);assert grade['result']['acceptance'] is False
    REPORT['submission']={'attempt_id':e['attempt_id'],'receipt':submit['receipt'],'grade_job_id':submit['grade_job_id'],'file_sha256':sha(code)}
    feed=req('GET','/v2/progress');assert all(r['attempt_id'] not in {x['attempt_id'] for x in entries} for r in feed['attempts'])
    REPORT['checks']['QA_excluded_from_genuine_totals']=True
    REPORT['checks']['public_registration_progress_code_media_return_grade']=True
    REPORT['finished_at']=time.time();REPORT['passed']=True
try:
    main()
finally:
    with open('acceptance.json','w') as f:json.dump(REPORT,f,indent=2)
print(json.dumps({'passed':REPORT.get('passed',False),'entries':len(REPORT.get('registration_receipts',[])),'media':{k:REPORT['media'][k] for k in ('bytes','sha256')} if 'media' in REPORT else None}))
