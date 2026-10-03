"""Rehearse Contacts-only rollback with a disposable contact."""
import json
import uuid
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:12347'
module = 'http://127.0.0.1:18080'
path = '/api/v1/contactservice/contacts'
record = {'accountId': str(uuid.uuid4()), 'name': 'Migration Rollback',
          'documentType': 1, 'documentNumber': 'MIGRATION-ROLLBACK-' + uuid.uuid4().hex,
          'phoneNumber': '0000000000'}
results = []
contact_id = None

def call(host, suffix='', method='GET', body=None):
    return request(host, path + suffix, method, body, test_token())

def check(label, ok):
    results.append({'step': label, 'passed': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + label, flush=True)
    if not ok:
        raise AssertionError(label)

assert json.loads(routing.DEFS['contacts']['file'].read_text())['mode'] == 'module'
try:
    status, result = call(base, method='POST', body=record)
    check('module creates disposable contact', status == 201 and result['status'] == 1)
    contact_id = result['data']['id']
    routing.switch('contacts', 'legacy')
    status, result = call(base, '/' + contact_id)
    check('legacy reads module-created contact', status == 200 and result['data']['name'] == record['name'])
    changed = dict(record, id=contact_id, name='Migration Rollback Updated')
    check('module write gate closes during rollback',
          call(module, method='PUT', body=changed)[0] == 503)
    status, result = call(base, method='PUT', body=changed)
    check('legacy updates disposable contact', status == 200 and result['status'] == 1)
    routing.switch('contacts', 'module')
    status, result = call(base, '/' + contact_id)
    check('module reads legacy-updated contact', status == 200
          and result['data']['name'] == changed['name'])
finally:
    if json.loads(routing.DEFS['contacts']['file'].read_text())['mode'] != 'module':
        routing.switch('contacts', 'module')
    if contact_id and call(base, '/' + contact_id)[1]['status'] == 1:
        call(base, '/' + contact_id, method='DELETE')

check('disposable contact removed', call(base, '/' + contact_id)[1]['status'] == 0)
output = root / 'ts-modulith/target/evidence/contacts-rollback.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Contacts rollback rehearsal passed')
