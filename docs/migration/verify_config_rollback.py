"""Rehearse Config-only rollback using a disposable config record."""
import json
import uuid
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
NAME = 'migration-rollback-' + uuid.uuid4().hex
PATH = '/api/v1/configservice/configs'
BASE = 'http://127.0.0.1:15679'
MODULE = 'http://127.0.0.1:18080'
initial = {'name': NAME, 'value': 'before', 'description': 'disposable rollback check'}
changed = {**initial, 'value': 'after'}
checks = []


def call(base, suffix='', method='GET', body=None):
    return request(base, PATH + suffix, method=method, body=body, token=test_token())


def check(label, value):
    checks.append({'step': label, 'passed': bool(value)})
    print(('PASS' if value else 'FAIL') + ' ' + label, flush=True)
    if not value:
        raise AssertionError(label)


assert json.loads(routing.DEFS['config']['file'].read_text())['mode'] == 'module'
try:
    status, result = call(BASE, method='POST', body=initial)
    check('module creates synthetic Config', status == 201 and result['status'] == 1)
    routing.switch('config', 'legacy')
    status, result = call(BASE, '/' + NAME)
    check('legacy reads module-created Config', status == 200 and result['data'] == initial)
    check('module write gate closes during rollback', call(MODULE, method='PUT', body=initial)[0] == 503)
    status, result = call(BASE, method='PUT', body=changed)
    check('legacy updates synthetic Config', status == 200 and result['status'] == 1)
    routing.switch('config', 'module')
    status, result = call(BASE, '/' + NAME)
    check('module reads legacy-updated Config', status == 200 and result['data'] == changed)
finally:
    if json.loads(routing.DEFS['config']['file'].read_text())['mode'] != 'module':
        routing.switch('config', 'module')
    if call(BASE, '/' + NAME)[1]['status'] == 1:
        call(BASE, '/' + NAME, method='DELETE')

check('synthetic Config removed', call(BASE, '/' + NAME)[1]['status'] == 0)
output = ROOT / 'ts-modulith/target/evidence/config-rollback.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Config rollback rehearsal passed')
