"""Switch only Admin Order to legacy and back without live writes."""
import json
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:16112'
prefix = '/api/v1/adminorderservice'
checks = []

def check(label, passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def probe(mode):
    req = urllib.request.Request(base+prefix+'/adminorder',
          headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        body = json.load(response)
        check(mode+' serves combined order list',response.status == 200 and
              response.headers.get('X-AdminOrder-Backend') == mode and
              body['status'] == 1 and len(body['data']) >= 100)
    check(mode+' protects reads',request(base,prefix+'/adminorder')[0] == 403)

if json.loads(routing.DEFS['adminorder']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Admin Order must start in module mode')
probe('module')
try:
    routing.switch('adminorder','legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['adminorder']['file'].read_text())['mode'] != 'module':
        routing.switch('adminorder','module')
probe('module')
output = root/'ts-modulith/target/evidence/admin-order-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Admin Order rollback rehearsal passed')
