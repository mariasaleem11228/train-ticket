"""Compare deployed Config with the isolated module; keep live Config read-only."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
LEGACY = 'http://127.0.0.1:25679'
MODULE = 'http://127.0.0.1:18087'
CANDIDATE = 'http://127.0.0.1:18086'
LIVE = 'http://127.0.0.1:15679'
PATH = '/api/v1/configservice/configs'
checks = []


def check(label, condition):
    checks.append({'step': label, 'passed': bool(condition)})
    print(('PASS' if condition else 'FAIL') + ' ' + label, flush=True)
    if not condition:
        raise AssertionError(label)


def call(base, suffix='', method='GET', body=None):
    return request(base, PATH + suffix, method=method, body=body, token=test_token())


def compare(label, suffix='', method='GET', body=None):
    old = call(LEGACY, suffix, method, body)
    new = call(MODULE, suffix, method, body)
    check(label, old == new)
    return old


def sorted_configs(result):
    status, body = result
    if isinstance(body, dict) and isinstance(body.get('data'), list):
        body['data'].sort(key=lambda config: config['name'])
    return status, body


legacy_baseline = call(LEGACY)
live_baseline = call(LIVE)
check('legacy test baseline is available', legacy_baseline[0] == 200 and legacy_baseline[1]['status'] == 1)
check('live Config remains available', live_baseline[0] == 200 and live_baseline[1]['status'] == 1)
check('read-only candidate matches live Config', call(CANDIDATE) == live_baseline)
check('Spring Modulith candidate has four modules',
      set(request(CANDIDATE, '/actuator/modulith')[1]) == {'station', 'orders', 'orderother', 'config'})

for config in legacy_baseline[1]['data']:
    status, current = call(MODULE, '/' + config['name'])
    if current['status'] == 0:
        created = call(MODULE, method='POST', body=config)
        check('copy isolated baseline ' + config['name'], created[0] == 201 and created[1]['status'] == 1)
    else:
        check('isolated baseline already matches ' + config['name'], current['data'] == config)

check('all configs match', sorted_configs(call(LEGACY)) == sorted_configs(call(MODULE)))
check('welcome matches', request(LEGACY, '/api/v1/configservice/welcome') ==
      request(MODULE, '/api/v1/configservice/welcome'))
compare('existing config matches', '/' + legacy_baseline[1]['data'][0]['name'])
compare('missing config matches', '/migration-does-not-exist')
name = 'migration-check-' + uuid.uuid4().hex
first = {'name': name, 'value': '0.25', 'description': 'isolated Config comparison'}
changed = {**first, 'value': '0.75'}
try:
    compare('create matches', method='POST', body=first)
    compare('duplicate create matches', method='POST', body=first)
    compare('created config matches', '/' + name)
    compare('update matches', method='PUT', body=changed)
    compare('updated config matches', '/' + name)
    compare('delete matches', '/' + name, method='DELETE')
    compare('missing delete matches', '/' + name, method='DELETE')
    compare('deleted config is absent', '/' + name)
    check('all configs match after isolated writes', sorted_configs(call(LEGACY)) == sorted_configs(call(MODULE)))
finally:
    for base in (LEGACY, MODULE):
        if call(base, '/' + name)[1]['status'] == 1:
            call(base, '/' + name, method='DELETE')

probe = 'migration-candidate-' + uuid.uuid4().hex
check('live candidate rejects writes', call(CANDIDATE, method='POST',
      body={'name': probe, 'value': 'x', 'description': 'write gate'})[0] == 503)
check('live Config unchanged by candidate', call(LIVE) == live_baseline)
output = ROOT / 'ts-modulith/target/evidence/config-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Config comparison passed:', len(checks), 'checks')
