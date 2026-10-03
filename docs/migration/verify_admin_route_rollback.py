"""Switch only Admin Route to legacy and back without live writes."""
import json
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:16113'
prefix = '/api/v1/adminrouteservice'
checks = []

def check(label, passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def probe(mode):
    req = urllib.request.Request(base+prefix+'/adminroute',
          headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        body = json.load(response)
        check(mode+' serves route catalogue',response.status == 200 and
              response.headers.get('X-AdminRoute-Backend') == mode and
              body['status'] == 1 and len(body['data']) >= 10)
    check(mode+' protects reads',request(base,prefix+'/adminroute')[0] == 403)

if json.loads(routing.DEFS['adminroute']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Admin Route must start in module mode')
probe('module')
try:
    routing.switch('adminroute','legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['adminroute']['file'].read_text())['mode'] != 'module':
        routing.switch('adminroute','module')
probe('module')
output = root/'ts-modulith/target/evidence/admin-route-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Admin Route rollback rehearsal passed')
