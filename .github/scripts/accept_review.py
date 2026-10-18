"""Anonymous off-machine public review acceptance; no service mutations."""
import concurrent.futures,hashlib,json,urllib.request,time
BASE='https://etaing4.github.io/joi-workbench-entry/review/'
def get(url):
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url,timeout=180) as r:
        assert r.status==200
        b=r.read(268435457);assert len(b)<=268435456;return b
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=json.loads(get(BASE+'checksums.json'));out=[]
for name,h in checks.items():
    b=get(BASE+name);assert sha(b)==h,(name,sha(b),h);out.append({'url':BASE+name,'sha256':h,'bytes':len(b)})
packet=json.loads(get(BASE+'review-packet.json'));assert len(packet['baseline']['cells'])==70 and len(packet['videos'])==10 and not packet['publication_blockers']
def asset(a):
    b=get(a['url']);assert sha(b)==a['sha256'],a['id'];return {'id':a['id'],'url':a['url'],'sha256':sha(b),'bytes':len(b)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:downloads=list(pool.map(asset,packet['assets']))
report={'passed':True,'at':time.time(),'client':'GitHub Actions ubuntu-latest stdlib; no authentication headers/cookies, checkout credentials not persisted','public_review_url':BASE,'packet_sha256':sha(get(BASE+'review-packet.json')),'baseline_cells':70,'supplied_films':len(packet['videos']),'static_checks':out,'exact_asset_readbacks':downloads,'scope':'anonymous HTTPS whole-file SHA readback; browser playback separately verified, no subjective/rights acceptance'}
with open('static-acceptance.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps({'passed':True,'films':len(packet['videos']),'assets_verified':len(downloads),'packet_sha256':report['packet_sha256']}))
