"""Rehearse User-only rollback without creating live identities."""
import json
import uuid
import urllib.request
from pathlib import Path

import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:12342'
prefix='/api/v1/userservice/users'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def probe(mode):
    with urllib.request.urlopen(base+prefix+'/hello',timeout=20) as response:
        check(mode+' serves User',response.status==200 and response.read()==b'Hello' and
              response.headers.get('X-User-Backend')==mode)
    status,body=request(base,prefix+'/fdse_microservice')
    check(mode+' reads existing profile',status==200 and body.get('status')==1 and
          body['data']['userId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f')

if json.loads(routing.DEFS['user']['file'].read_text())['mode']!='module':
    raise RuntimeError('User must start in module mode')
probe('module')
try:
    routing.switch('user','legacy')
    probe('legacy')
    check('inactive module refuses registration',request('http://127.0.0.1:18080',
          prefix+'/register','POST',{'userId':str(uuid.uuid4()),
          'userName':'migration-disabled-write','password':'never-created'})[0]==503)
finally:
    if json.loads(routing.DEFS['user']['file'].read_text())['mode']!='module':
        routing.switch('user','module')
probe('module')
output=root/'ts-modulith/target/evidence/user-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('User rollback rehearsal passed')
