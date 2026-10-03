"""Switch only Admin Basic Info to legacy and back without live writes."""
import json
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:18767'
prefix = '/api/v1/adminbasicservice/adminbasic/'
checks = []

def check(label, passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label,flush=True)
    if not passed: raise AssertionError(label)

def probe(mode):
    for name in ('contacts','stations','trains','configs','prices'):
        with urllib.request.urlopen(base+prefix+name,timeout=20) as response:
            payload = json.load(response)
            check(mode+' '+name+' route',response.status == 200 and
                  response.headers.get('X-AdminBasic-Backend') == mode and
                  payload['status'] == 1)
    check(mode+' protects writes',request(base,prefix+'configs','POST',
          {'name':'blocked','value':'1'},token=test_token('ROLE_USER'))[0] == 403)

if json.loads(routing.DEFS['adminbasic']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Admin Basic Info must start in module mode')
probe('module')
try:
    routing.switch('adminbasic','legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['adminbasic']['file'].read_text())['mode'] != 'module':
        routing.switch('adminbasic','module')
probe('module')
output = root/'ts-modulith/target/evidence/admin-basic-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Admin Basic Info rollback rehearsal passed')
