"""Rehearse Consign rollback using one removable synthetic shipment."""
import json
import subprocess
import urllib.request
import uuid
from pathlib import Path

import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:16111'
prefix = '/api/v1/consignservice'
token = test_token('ROLE_USER')
marker = 'migration-consign-rollback-' + uuid.uuid4().hex
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

def call(path, method='GET', body=None, host=base):
    return request(host, prefix + path, method, body, token)

def backend():
    req = urllib.request.Request(base + prefix + '/welcome',
                                 headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.status, response.headers.get('X-Consign-Backend')

def cleanup():
    names = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    matches = [name for name in names if name.endswith('train-ticket-ts-consign-mongo-1')]
    if len(matches) != 1:
        raise RuntimeError('Expected one Consign Mongo container')
    js = 'db.getSiblingDB("ts").consign_record.deleteOne({consignee:"' + marker + '"})'
    return subprocess.check_output(['docker', 'exec', matches[0], 'mongo', '--quiet', '--eval', js], text=True)

if json.loads(routing.DEFS['consign']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Consign must start in module mode')

record_id = None
try:
    check('module serves Consign', backend() == (200, 'module'))
    status, created = call('/consigns', 'PUT', payload)
    if isinstance(created, dict) and isinstance(created.get('data'), dict):
        record_id = created['data'].get('id')
    check('module creates synthetic consignment',
          status == 200 and created['status'] == 1 and record_id and created['data']['price'] == 16.0)
    routing.switch('consign', 'legacy')
    check('legacy serves Consign', backend() == (200, 'legacy'))
    status, retained = call('/consigns/order/' + order_id)
    check('legacy sees module-created consignment',
          status == 200 and retained['status'] == 1 and retained['data']['id'] == record_id)
    check('inactive module rejects writes',
          call('/consigns', 'PUT', payload, 'http://127.0.0.1:18080')[0] == 503)
    update = dict(payload, id=record_id, weight=4.0)
    status, changed = call('/consigns', 'PUT', update)
    check('legacy updates synthetic consignment',
          status == 200 and changed['status'] == 1 and changed['data']['price'] == 20.0)
finally:
    if json.loads(routing.DEFS['consign']['file'].read_text())['mode'] != 'module':
        routing.switch('consign', 'module')
    if record_id:
        status, retained = call('/consigns/order/' + order_id)
        check('module sees legacy update',
              status == 200 and retained['status'] == 1 and retained['data']['price'] == 20.0)
        check('synthetic consignment removed', '"deletedCount" : 1' in cleanup())

check('module serves Consign again', backend() == (200, 'module'))
output = root / 'ts-modulith/target/evidence/consign-rollback.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Consign rollback rehearsal passed')
