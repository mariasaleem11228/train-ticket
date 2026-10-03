"""Exercise a uniquely named Station fixture through Admin and verify rollback data.

Run create in module mode, rollback in legacy mode, then cleanup in module mode.
Only the fixture named in target/evidence/cutover-fixture.json is changed.
"""
import argparse
import json
import uuid
from pathlib import Path
from http_support import request, test_token

OUT = Path(__file__).resolve().parents[2] / 'ts-modulith/target/evidence'
parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['create', 'rollback', 'cleanup'])
args = parser.parse_args()
state = json.loads((OUT.parents[2] / 'deployment/migration/.state/routing-state.json').read_text())
expected_mode = 'legacy' if args.action == 'rollback' else 'module'
assert state['mode'] == expected_mode, state
fixture_path = OUT / 'cutover-fixture.json'
token = test_token()
base = 'http://127.0.0.1:18767'
path = '/api/v1/adminbasicservice/adminbasic/stations'
results = []
if args.action == 'create':
    if fixture_path.exists():
        raise RuntimeError('Existing fixture state: finish cleanup before creating another fixture.')
    fixture = {'id': 'migration-' + uuid.uuid4().hex, 'name': 'Migration rollback fixture', 'stayTime': 11}
    fixture_path.write_text(json.dumps(fixture), encoding='utf-8')
    status, data = request(base, path, 'POST', fixture, token)
    assert status == 200 and data['status'] == 1, (status, data)
    results.append({'operation': 'create through existing Admin service', 'passed': True})
else:
    fixture = json.loads(fixture_path.read_text())
status, data = request('http://127.0.0.1:12345', '/api/v1/stationservice/stations/name/' + fixture['id'])
assert status == 200 and data['data'] == fixture['name'], (status, data)
results.append({'operation': 'read module-created record in ' + state['mode'], 'passed': True})
if args.action == 'rollback':
    fixture['name'] += ' updated by legacy'
    fixture['stayTime'] = 12
    status, data = request(base, path, 'PUT', fixture, token)
    assert status == 200 and data['status'] == 1, (status, data)
    fixture_path.write_text(json.dumps(fixture), encoding='utf-8')
    results.append({'operation': 'update module-created record through legacy', 'passed': True})
if args.action == 'cleanup':
    status, data = request(base, path, 'DELETE', fixture, token)
    assert status == 200 and data['status'] == 1, (status, data)
    assert request('http://127.0.0.1:12345', '/api/v1/stationservice/stations/name/' + fixture['id'])[1]['status'] == 0
    results.append({'operation': 'delete only migration fixture through Admin', 'passed': True})
(OUT / ('cutover-' + args.action + '.json')).write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
