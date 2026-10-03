"""Exercise independent Assurance rollback and shared-data retention."""
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:18888'
prefix='/api/v1/assuranceservice'
token=test_token('ROLE_USER')
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def backend():
    req=urllib.request.Request(base+prefix+'/welcome',headers={'Authorization':'Bearer '+token})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-Assurance-Backend'),response.read().decode()
def call(path,method='GET',host=base):return request(host,prefix+path,method,token=token)

if json.loads(routing.DEFS['assurance']['file'].read_text())['mode']!='module':
    raise RuntimeError('Assurance must start in module mode')
identity='Welcome to [ Assurance Service ] !'
check('module serves Assurance',backend()==(200,'module',identity))
order=str(uuid.uuid4())
status,created=call('/assurances/1/'+order)
check('module creates synthetic assurance',status==200 and created['status']==1)
assurance_id=created['data']['id']
try:
    routing.switch('assurance','legacy')
    check('legacy serves Assurance',backend()==(200,'legacy',identity))
    check('legacy sees module-created insurance',call('/assurance/orderid/'+order)[1]['data']['id']==assurance_id)
    blocked=str(uuid.uuid4())
    check('inactive module rejects writes',call('/assurances/1/'+blocked,host='http://127.0.0.1:18080')[0]==503)
    check('rejected write left no record',call('/assurance/orderid/'+blocked)[1]['status']==0)
    check('legacy removes synthetic insurance',call('/assurances/orderid/'+order,'DELETE')[1]['status']==1)
finally:
    if json.loads(routing.DEFS['assurance']['file'].read_text())['mode']!='module':
        routing.switch('assurance','module')
check('module serves Assurance again',backend()==(200,'module',identity))
check('module sees legacy deletion',call('/assurance/orderid/'+order)[1]['status']==0)
check('insurance types retained',call('/assurances/types')[1]['data'][0]['index']==1)
output=root/'ts-modulith/target/evidence/assurance-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Assurance rollback rehearsal passed')
