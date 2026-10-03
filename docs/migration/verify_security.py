"""Compare Security with isolated MongoDB copies and a read-only live candidate."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
LEGACY = 'http://127.0.0.1:21188'
MODULE = 'http://127.0.0.1:18090'
CANDIDATE = 'http://127.0.0.1:18089'
LIVE = 'http://127.0.0.1:11188'
PATH = '/api/v1/securityservice/securityConfigs'
checks = []


def call(base, suffix='', method='GET', body=None):
    return request(base, PATH + suffix, method, body, test_token())


def check(label, condition):
    checks.append({'step': label, 'passed': bool(condition)})
    print(('PASS' if condition else 'FAIL') + ' ' + label, flush=True)
    if not condition:
        raise AssertionError(label)


def normal(result):
    status, body = result
    if isinstance(body, dict) and isinstance(body.get('data'), list):
        body['data'].sort(key=lambda policy: policy['name'])
    return status, body


fixture = json.loads((ROOT/'deployment/migration/.state/e2e/fixture.json').read_text())
live_before = call(LIVE)
check('read-only candidate matches live policies', normal(call(CANDIDATE)) == normal(live_before))
check('candidate has six Spring Modulith modules',
      set(request(CANDIDATE, '/actuator/modulith')[1]) ==
      {'station', 'orders', 'orderother', 'config', 'seat', 'security'})
check('isolated baseline records match', normal(call(LEGACY)) == normal(call(MODULE)))
check('booking policy decision matches for test account',
      call(LEGACY, '/' + fixture['userId']) == call(MODULE, '/' + fixture['userId']))
check('booking policy decision matches for unknown account',
      call(LEGACY, '/' + str(uuid.uuid4()))[1]['status'] == 1 and
      call(MODULE, '/' + str(uuid.uuid4()))[1]['status'] == 1)
check('welcome matches', request(LEGACY, '/api/v1/securityservice/welcome', token=test_token()) ==
      request(MODULE, '/api/v1/securityservice/welcome', token=test_token()))

name = 'migration-security-' + uuid.uuid4().hex
body = {'name': name, 'value': '3', 'description': 'isolated comparison'}
old_id = new_id = None
try:
    old = call(LEGACY, method='POST', body=body)
    new = call(MODULE, method='POST', body=body)
    check('create response and fields match', old[0] == new[0] == 200 and
          old[1]['status'] == new[1]['status'] == 1 and
          {k:v for k,v in old[1]['data'].items() if k != 'id'} ==
          {k:v for k,v in new[1]['data'].items() if k != 'id'})
    old_id, new_id = old[1]['data']['id'], new[1]['data']['id']
    check('created IDs are UUIDs', bool(uuid.UUID(old_id)) and bool(uuid.UUID(new_id)))
    check('duplicate create matches', call(LEGACY, method='POST', body=body) ==
          call(MODULE, method='POST', body=body))
    changed = {**body, 'value': '4'}
    old = call(LEGACY, method='PUT', body={**changed, 'id': old_id})
    new = call(MODULE, method='PUT', body={**changed, 'id': new_id})
    check('update response matches', old[0] == new[0] == 200 and
          old[1]['status'] == new[1]['status'] == 1 and
          {k:v for k,v in old[1]['data'].items() if k != 'id'} ==
          {k:v for k,v in new[1]['data'].items() if k != 'id'})
    check('updated records match',
          next(x for x in call(LEGACY)[1]['data'] if x['name'] == name)['value'] ==
          next(x for x in call(MODULE)[1]['data'] if x['name'] == name)['value'] == '4')
    check('delete matches',
          call(LEGACY, '/' + old_id, 'DELETE')[1]['status'] ==
          call(MODULE, '/' + new_id, 'DELETE')[1]['status'] == 1)
    check('isolated baseline restored', normal(call(LEGACY)) == normal(call(MODULE)))
finally:
    for base, policy_id in ((LEGACY, old_id), (MODULE, new_id)):
        if policy_id and any(x['name'] == name for x in call(base)[1].get('data') or []):
            call(base, '/' + policy_id, 'DELETE')

probe = {'name': 'migration-readonly-' + uuid.uuid4().hex,
         'value': '1', 'description': 'write gate'}
check('candidate rejects writes', call(CANDIDATE, method='POST', body=probe)[0] == 503)
check('live policies unchanged', normal(call(LIVE)) == normal(live_before))
output = ROOT/'ts-modulith/target/evidence/security-comparison.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Security comparison passed:', len(checks), 'checks')
