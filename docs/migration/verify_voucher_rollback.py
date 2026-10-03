"""Switch Voucher module to deployed Python service and back using a cached voucher."""
import json
import urllib.request
from pathlib import Path
import hybrid_routing as routing

root = Path(__file__).resolve().parents[2]
payload = json.loads((routing.STATE/'e2e/voucher.json').read_text())
checks = []

def check(label, passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def probe(mode):
    req = urllib.request.Request('http://127.0.0.1:16101/getVoucher',
          data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as response:
        body=json.load(response)
        check(mode+' serves cached voucher',response.status==200 and
              response.headers.get('X-Voucher-Backend')==mode and
              body['order_id']==payload['orderId'])

if json.loads(routing.DEFS['voucher']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Voucher must start in module mode')
probe('module')
try:
    routing.switch('voucher','legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['voucher']['file'].read_text())['mode'] != 'module':
        routing.switch('voucher','module')
probe('module')
output = root/'ts-modulith/target/evidence/voucher-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Voucher rollback rehearsal passed')
