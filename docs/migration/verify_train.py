"""Compare Train's deployed contract on copied data and read-only live data."""
import json
import uuid
from pathlib import Path
from http_support import request, wait_ready

ROOT = Path(__file__).resolve().parents[2]
PATH = '/api/v1/trainservice/trains'
LEGACY = 'http://127.0.0.1:24567'
MODULE = 'http://127.0.0.1:18092'
CANDIDATE = 'http://127.0.0.1:18091'
LIVE = 'http://127.0.0.1:14567'
checks = []

def call(base, suffix='', method='GET', body=None):
    return request(base, PATH + suffix, method, body)

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS' if passed else 'FAIL') + ' ' + label, flush=True)
    if not passed:
        raise AssertionError(label)

def sorted_list(response):
    status, body = response
    if isinstance(body, dict) and isinstance(body.get('data'), list):
        body['data'].sort(key=lambda train: train['id'])
    return status, body

for base in (LEGACY, MODULE, CANDIDATE):
    wait_ready(base, '/api/v1/trainservice/trains/welcome', 300)

live_before = sorted_list(call(LIVE))
check('live catalogue has six records', live_before[0] == 200 and len(live_before[1]['data']) == 6)
check('read-only candidate matches live catalogue', sorted_list(call(CANDIDATE)) == live_before)
check('isolated legacy and module data match', sorted_list(call(LEGACY)) == sorted_list(call(MODULE)))
check('welcome matches', request(LEGACY, PATH + '/welcome') == request(MODULE, PATH + '/welcome'))
for train in live_before[1]['data']:
    check('existing train ' + train['id'], call(LEGACY, '/' + train['id']) == call(MODULE, '/' + train['id']))
check('missing train matches', call(LEGACY, '/migration-missing') == call(MODULE, '/migration-missing'))
check('candidate rejects writes', call(CANDIDATE, method='POST',
      body={'id': 'migration-readonly-' + uuid.uuid4().hex})[0] == 503)

name = 'migration-train-' + uuid.uuid4().hex
original = {'id': name, 'economyClass': 14, 'confortClass': 7, 'averageSpeed': 140}
updated = {**original, 'economyClass': 13, 'averageSpeed': 160}
try:
    for label, suffix, method, body in (
            ('create', '', 'POST', original),
            ('duplicate create', '', 'POST', original),
            ('created record', '/' + name, 'GET', None),
            ('update', '', 'PUT', updated),
            ('updated record', '/' + name, 'GET', None),
            ('delete', '/' + name, 'DELETE', None),
            ('missing delete', '/' + name, 'DELETE', None)):
        check(label + ' matches', call(LEGACY, suffix, method, body) == call(MODULE, suffix, method, body))
    check('isolated baselines restored', sorted_list(call(LEGACY)) == sorted_list(call(MODULE)))
finally:
    for base in (LEGACY, MODULE):
        if call(base, '/' + name)[1].get('status') == 1:
            call(base, '/' + name, 'DELETE')
check('live catalogue unchanged', sorted_list(call(LIVE)) == live_before)
check('Spring Modulith declares Train', 'train' in request(CANDIDATE, '/actuator/modulith')[1])
output = ROOT/'ts-modulith/target/evidence/train-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Train comparison passed:', len(checks), 'checks')
