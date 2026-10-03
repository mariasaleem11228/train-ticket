"""Rehearse Auth-only rollback with read-only login requests."""
import json
import urllib.request
from pathlib import Path

import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:12340'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def probe(mode):
    with urllib.request.urlopen(base+'/api/v1/auth/hello',timeout=20) as response:
        check(mode+' serves Auth',response.status==200 and response.read()==b'hello' and
              response.headers.get('X-Auth-Backend')==mode)
    status,body=request(base,'/api/v1/users/login','POST',
                        {'username':'fdse_microservice','password':'111111','verificationCode':'WRONG'})
    check(mode+' logs in through Verification Code',status==200 and body.get('status')==1 and
          body['data']['userId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f')

if json.loads(routing.DEFS['auth']['file'].read_text())['mode']!='module':
    raise RuntimeError('Auth must start in module mode')
probe('module')
try:
    routing.switch('auth','legacy')
    probe('legacy')
    check('inactive module refuses registration',request('http://127.0.0.1:18080',
          '/api/v1/auth','POST',{'userId':'00000000-0000-0000-0000-000000000000',
          'userName':'migration-disabled-write','password':'never-created'})[0]==503)
finally:
    if json.loads(routing.DEFS['auth']['file'].read_text())['mode']!='module':
        routing.switch('auth','module')
probe('module')
output=root/'ts-modulith/target/evidence/auth-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Auth rollback rehearsal passed')
