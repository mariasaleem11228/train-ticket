"""Rehearse Security-only rollback with a disposable policy record."""
import json
import uuid
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
NAME = 'migration-security-rollback-' + uuid.uuid4().hex
PATH = '/api/v1/securityservice/securityConfigs'
BASE = 'http://127.0.0.1:11188'
MODULE = 'http://127.0.0.1:18080'
initial = {'name': NAME, 'value': '3', 'description': 'disposable rollback check'}
checks = []
policy_id = None


def call(base, suffix='', method='GET', body=None):
    return request(base, PATH + suffix, method, body, test_token())


def find(base):
    return next((item for item in call(base)[1].get('data') or [] if item['name'] == NAME), None)


def check(label, condition):
    checks.append({'step': label, 'passed': bool(condition)})
    print(('PASS' if condition else 'FAIL') + ' ' + label, flush=True)
    if not condition:
        raise AssertionError(label)


assert json.loads(routing.DEFS['security']['file'].read_text())['mode'] == 'module'
try:
    status, response = call(BASE, method='POST', body=initial)
    check('module creates synthetic Security policy', status == 200 and response['status'] == 1)
    policy_id = response['data']['id']
    routing.switch('security', 'legacy')
    check('legacy reads module-created policy', find(BASE) == response['data'])
    check('module write gate closes during rollback',
          call(MODULE, method='PUT', body={**initial, 'id': policy_id})[0] == 503)
    status, updated = call(BASE, method='PUT', body={**initial, 'id': policy_id, 'value': '4'})
    check('legacy updates synthetic policy', status == 200 and updated['status'] == 1)
    routing.switch('security', 'module')
    check('module reads legacy-updated policy', find(BASE) == updated['data'])
finally:
    if json.loads(routing.DEFS['security']['file'].read_text())['mode'] != 'module':
        routing.switch('security', 'module')
    if policy_id and find(BASE):
        call(BASE, '/' + policy_id, method='DELETE')

check('synthetic policy removed', find(BASE) is None)
output = ROOT/'ts-modulith/target/evidence/security-rollback.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Security rollback rehearsal passed')
