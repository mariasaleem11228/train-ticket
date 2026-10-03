"""Compare deployed Route and module using copied Mongo data and a read-only live candidate."""
import json
import uuid
from pathlib import Path
from http_support import request, wait_ready

ROOT=Path(__file__).resolve().parents[2]
PATH='/api/v1/routeservice/routes'
LEGACY='http://127.0.0.1:21178'
MODULE='http://127.0.0.1:18094'
CANDIDATE='http://127.0.0.1:18093'
LIVE='http://127.0.0.1:11178'
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
        body['data'].sort(key=lambda route:route['id'])
    return status,body

for base in (LEGACY,MODULE,CANDIDATE):
    wait_ready(base,'/api/v1/routeservice/welcome',300)
live_before=normal(call(LIVE))
check('live routes available',live_before[0]==200 and len(live_before[1]['data'])==10)
check('read-only candidate matches live',normal(call(CANDIDATE))==live_before)
check('isolated copies match',normal(call(LEGACY))==normal(call(MODULE)))
check('welcome matches',request(LEGACY,'/api/v1/routeservice/welcome')==
      request(MODULE,'/api/v1/routeservice/welcome'))
for route in live_before[1]['data']:
    check('route by ID '+route['id'],call(LEGACY,'/'+route['id'])==call(MODULE,'/'+route['id']))
for start,end in [('nanjing','shanghai'),('shanghai','nanjing'),('shanghai','beijing'),
                  ('unknown','shanghai')]:
    check('station pair '+start+'/'+end,normal(call(LEGACY,'/'+start+'/'+end))==
          normal(call(MODULE,'/'+start+'/'+end)))
check('missing route matches',call(LEGACY,'/migration-missing')==call(MODULE,'/migration-missing'))

invalid={'id':'short','startStation':'a','endStation':'b','stationList':'a,b','distanceList':'0'}
check('anonymous validation matches',call(LEGACY,method='POST',body=invalid)==
      call(MODULE,method='POST',body=invalid))
new={'id':'migration-route-'+uuid.uuid4().hex,'startStation':'a','endStation':'b',
     'stationList':'a,b','distanceList':'0,10'}
changed={**new,'distanceList':'0,20'}
check('candidate rejects writes',call(CANDIDATE,method='POST',body=new)[0]==503)
try:
    for label,suffix,method,body in (
            ('create given ID','','POST',new),
            ('created record','/'+new['id'],'GET',None),
            ('modify','','POST',changed),
            ('modified record','/'+new['id'],'GET',None),
            ('delete','/'+new['id'],'DELETE',None),
            ('missing delete','/'+new['id'],'DELETE',None)):
        check(label+' matches',call(LEGACY,suffix,method,body)==call(MODULE,suffix,method,body))
    check('isolated datasets restored',normal(call(LEGACY))==normal(call(MODULE)))
finally:
    for base in (LEGACY,MODULE):
        if call(base,'/'+new['id'])[1].get('status')==1:
            call(base,'/'+new['id'],'DELETE')
check('live dataset unchanged',normal(call(LIVE))==live_before)
check('Spring Modulith declares Route','route' in request(CANDIDATE,'/actuator/modulith')[1])
output=ROOT/'ts-modulith/target/evidence/route-comparison.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Route comparison passed:',len(checks),'checks')
