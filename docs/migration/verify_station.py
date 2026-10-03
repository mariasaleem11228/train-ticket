"""Differential tests against isolated legacy/module databases. Never use live URLs.

Defaults refer to compose.station.yml's isolated test containers. Mutating tests
are intentionally restricted to these loopback ports and use unique fixture IDs.
"""
import json
import uuid
from pathlib import Path
from urllib.parse import quote
from http_support import request, test_token, wait_ready

ROOT = Path(__file__).resolve().parents[2]
OLD = 'http://127.0.0.1:22345'
NEW = 'http://127.0.0.1:18081'
PREFIX = '/api/v1/stationservice'
ADMIN = test_token()
results = []
wait_ready(OLD)
wait_ready(NEW)

def compare(label, path, method='GET', body=None, token=None, status_only=False, expected_statuses=None):
    old = request(OLD, PREFIX + path, method, body, token)
    new = request(NEW, PREFIX + path, method, body, token)
    if path == '/stations' and method == 'GET' and old[0] == new[0] == 200:
        for response in (old, new):
            if isinstance(response[1].get('data'), list):
                response[1]['data'].sort(key=lambda item: item['id'])
    passed = old[0] == new[0] if status_only else old == new
    if expected_statuses:
        passed = (old[0], new[0]) == expected_statuses
    results.append(dict(label=label, passed=passed, equivalent=old == new,
                        intentional_difference=bool(expected_statuses), legacy=old, module=new))
    print(('PASS' if passed else 'FAIL'), label)
    return new

compare('welcome', '/welcome')
compare('all stations', '/stations')
for name in ['Shang Hai', 'shanghai', 'missing station', 'München']:
    compare('name lookup ' + name, '/stations/id/' + quote(name))
for identifier in ['shanghai', 'unknown']:
    compare('id lookup ' + identifier, '/stations/name/' + identifier)
for names in [[], ['Shang Hai', 'missing', 'Shang Hai']]:
    compare('batch IDs ' + repr(names), '/stations/idlist', 'POST', names)
for ids in [[], ['shanghai', 'missing', 'shanghai'], ['missing']]:
    compare('batch names ' + repr(ids), '/stations/namelist', 'POST', ids)
fixture = {'id': 'migration-' + uuid.uuid4().hex, 'name': 'Migration München Station', 'stayTime': 9}
try:
    for verb in ['POST', 'PUT', 'DELETE']:
        compare('anonymous ' + verb, '/stations', verb, fixture, status_only=True)
        compare('user ' + verb, '/stations', verb, fixture, test_token('ROLE_USER'), status_only=True)
    compare('invalid JWT: explicit legacy defect correction (500 -> 401)', '/stations', token='invalid', expected_statuses=(500, 401))
    compare('create', '/stations', 'POST', fixture, ADMIN)
    compare('duplicate ID', '/stations', 'POST', fixture, ADMIN)
    compare('created lookup', '/stations/name/' + fixture['id'])
    fixture['name'] += ' Updated'
    fixture['stayTime'] = 17
    compare('update', '/stations', 'PUT', fixture, ADMIN)
    compare('updated lookup', '/stations/name/' + fixture['id'])
    compare('delete body', '/stations', 'DELETE', fixture, ADMIN)
    compare('delete missing', '/stations', 'DELETE', fixture, ADMIN)
    compare('update missing', '/stations', 'PUT', fixture, ADMIN)
finally:
    for base in (OLD, NEW):
        request(base, PREFIX + '/stations', 'DELETE', fixture, ADMIN)

hex_fixture = {'id': uuid.uuid4().hex[:24], 'name': 'Hex identifier fixture', 'stayTime': 3}
try:
    compare('hexadecimal ID create', '/stations', 'POST', hex_fixture, ADMIN)
    compare('hexadecimal ID lookup', '/stations/name/' + hex_fixture['id'])
    compare('hexadecimal ID list mapping', '/stations')
    compare('hexadecimal ID delete', '/stations', 'DELETE', hex_fixture, ADMIN)
finally:
    for base in (OLD, NEW):
        request(base, PREFIX + '/stations', 'DELETE', hex_fixture, ADMIN)

out = ROOT / 'ts-modulith/target/evidence/station-contracts.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
failed = sum(not result['passed'] for result in results)
print(f'{len(results) - failed}/{len(results)} comparisons passed; {out}')
raise SystemExit(bool(failed))
