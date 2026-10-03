"""Compare Price's deployed API on copied databases and a read-only live candidate."""
import json
import uuid
from pathlib import Path
from http_support import request,wait_ready

ROOT=Path(__file__).resolve().parents[2]
PATH='/api/v1/priceservice/prices'
LEGACY='http://127.0.0.1:26579'
MODULE='http://127.0.0.1:18096'
CANDIDATE='http://127.0.0.1:18095'
LIVE='http://127.0.0.1:16579'
checks=[]

def call(base,suffix='',method='GET',body=None):
    return request(base,PATH+suffix,method,body)

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS' if passed else 'FAIL')+' '+label,flush=True)
    if not passed:raise AssertionError(label)

def normal(value):
    status,body=value
    if isinstance(body,dict) and isinstance(body.get('data'),list):
        body['data'].sort(key=lambda config:config['id'])
    return status,body

for base in (LEGACY,MODULE,CANDIDATE):
    wait_ready(base,PATH+'/welcome',300)
live_before=normal(call(LIVE))
check('live catalogue has ten prices',live_before[0]==200 and len(live_before[1]['data'])==10)
check('read-only candidate matches live',normal(call(CANDIDATE))==live_before)
check('isolated copies match',normal(call(LEGACY))==normal(call(MODULE)))
check('welcome matches',request(LEGACY,PATH+'/welcome')==request(MODULE,PATH+'/welcome'))
for config in live_before[1]['data']:
    suffix='/'+config['routeId']+'/'+config['trainType']
    check('price for '+config['routeId'],call(LEGACY,suffix)==call(MODULE,suffix))
check('missing price matches',call(LEGACY,'/missing-route/missing-train')==
      call(MODULE,'/missing-route/missing-train'))
new={'id':str(uuid.uuid4()),'routeId':'migration-route-'+uuid.uuid4().hex,
     'trainType':'migration-train','basicPriceRate':0.31,'firstClassPriceRate':0.91}
changed={**new,'basicPriceRate':0.32}
lookup='/'+new['routeId']+'/'+new['trainType']
check('candidate rejects writes',call(CANDIDATE,method='POST',body=new)[0]==503)
try:
    for label,suffix,method,body in (
            ('create','','POST',new),
            ('created lookup',lookup,'GET',None),
            ('update','','PUT',changed),
            ('updated lookup',lookup,'GET',None),
            ('delete','','DELETE',changed),
            ('missing lookup',lookup,'GET',None),
            ('missing delete','','DELETE',changed)):
        check(label+' matches',call(LEGACY,suffix,method,body)==call(MODULE,suffix,method,body))
    check('isolated datasets restored',normal(call(LEGACY))==normal(call(MODULE)))
finally:
    for base in (LEGACY,MODULE):
        if call(base,lookup)[1].get('status')==1:
            call(base,method='DELETE',body=changed)
check('live catalogue unchanged',normal(call(LIVE))==live_before)
check('Spring Modulith declares Price','price' in request(CANDIDATE,'/actuator/modulith')[1])
output=ROOT/'ts-modulith/target/evidence/price-comparison.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Price comparison passed:',len(checks),'checks')
