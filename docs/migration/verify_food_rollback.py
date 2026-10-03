"""Rehearse Food-only rollback without publishing delivery messages."""
import json
import uuid
import urllib.request
from pathlib import Path

import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:18856'
prefix='/api/v1/foodservice'
menu='/foods/2026-10-03/Shang%20Hai/Su%20Zhou/D1345'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def backend():
    with urllib.request.urlopen(base+prefix+'/welcome',timeout=20) as response:
        return response.status,response.headers.get('X-Food-Backend')

if json.loads(routing.DEFS['food']['file'].read_text())['mode']!='module':
    raise RuntimeError('Food must start in module mode')
expected=request(base,prefix+menu)
check('module serves Food',backend()==(200,'module'))
try:
    routing.switch('food','legacy')
    check('legacy serves Food',backend()==(200,'legacy'))
    check('legacy retains Food menu',request(base,prefix+menu)==expected)
    sample={'orderId':str(uuid.uuid4()),'foodType':2,'stationName':'suzhou',
            'storeName':'Roman Holiday','foodName':'Bone Soup','price':2.5}
    check('inactive module rejects Food writes',
          request('http://127.0.0.1:18080',prefix+'/orders','POST',sample)[0]==503)
finally:
    if json.loads(routing.DEFS['food']['file'].read_text())['mode']!='module':
        routing.switch('food','module')
check('module serves Food again',backend()==(200,'module'))
check('module retains Food menu',request(base,prefix+menu)==expected)
output=root/'ts-modulith/target/evidence/food-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Food rollback rehearsal passed')
