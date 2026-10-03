"""Exercise the Consign UI write path through port 8080 and remove its test record."""
import json
import subprocess
import urllib.request
import uuid
from pathlib import Path

from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
prefix = '/api/v1/consignservice'
token = test_token('ROLE_USER')
marker = 'migration-consign-ui-' + uuid.uuid4().hex
order_id = str(uuid.uuid4())
payload = {'orderId': order_id, 'accountId': str(uuid.uuid4()),
           'handleDate': '2026-10-02', 'targetDate': '2026-10-03',
           'from': 'Shang Hai', 'to': 'Nan Jing', 'consignee': marker,
           'phone': '1234567890', 'weight': 3.0, 'isWithin': False}
checks = []

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

def cleanup():
    names = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    matches = [name for name in names if name.endswith('train-ticket-ts-consign-mongo-1')]
    if len(matches) != 1:
        raise RuntimeError('Expected one Consign Mongo container')
    js = 'db.getSiblingDB("ts").consign_record.deleteOne({consignee:"' + marker + '"})'
    return subprocess.check_output(['docker', 'exec', matches[0], 'mongo', '--quiet', '--eval', js], text=True)

record_id = None
try:
    req = urllib.request.Request('http://127.0.0.1:8080' + prefix + '/consigns',
                                 data=json.dumps(payload).encode(), method='PUT',
                                 headers={'Authorization': 'Bearer ' + token,
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        backend = response.headers.get('X-Consign-Backend')
        status = response.status
        result = json.load(response)
    if isinstance(result.get('data'), dict):
        record_id = result['data'].get('id')
    check('UI gateway routes Consign write to module',
          status == 200 and backend == 'module' and result['status'] == 1
          and record_id and result['data']['price'] == 16.0)
    status, found = request('http://127.0.0.1:8080', prefix + '/consigns/order/' + order_id,
                            token=token)
    check('UI gateway reads same shipment',
          status == 200 and found['status'] == 1 and found['data']['id'] == record_id)
finally:
    if record_id:
        check('synthetic shipment removed', '"deletedCount" : 1' in cleanup())

output = root / 'ts-modulith/target/evidence/consign-ui.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Consign UI route passed')
