"""Add Security to the live host while its original microservice remains routed."""
import json
import subprocess
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
names = ('station', 'orders', 'orderother', 'config', 'seat')
state_file = routing.STATE/'hybrid.json'
state = json.loads(state_file.read_text())
assert set(state['modules']) == set(names), 'Expected five-module Seat checkpoint'
for name in names:
    assert json.loads(routing.DEFS[name]['file'].read_text())['mode'] == 'module'
routing.require_gate('security-comparison.json', 15)
assert (routing.EVIDENCE/'security-backup.archive').stat().st_size > 0
target = routing.docker('image', 'inspect', 'train-ticket/ts-modulith:security-candidate', '--format', '{{.Id}}')
previous = routing.inspect(routing.station.MODULE)['Image']
assert target != previous
overlay = routing.STATE/'security-previous-image.yml'
overlay.write_text('services:\n  modulith:\n    image: '+previous+'\n')
routing.owner('security', 'legacy')
for name in names:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in names:
        routing.ready(name, routing.station.MODULE)
    status, result = request('http://127.0.0.1:18080',
                             '/api/v1/securityservice/securityConfigs', token=test_token())
    assert status == 200 and result['status'] == 1
    status, model = request('http://127.0.0.1:18080', '/actuator/modulith')
    assert status == 200 and set(model) == {*names, 'security'}
    for name in names:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
    state.update(stage='security', image=target, modules=[*names, 'security'])
    routing.write_json(state_file, state)
    routing.write_json(routing.STATE/'security-upgrade.json',
                       {'previous_image': previous, 'new_image': target, 'status': 'complete'})
    subprocess.run(['python', str(root/'docs/migration/verify_checkpoint.py')], check=True)
    print('Six-module host ready; Security still serves from its original service')
except Exception:
    routing.docker(*routing.COMPOSE, '-f', str(overlay), 'up', '-d', 'modulith')
    for name in names:
        routing.ready(name, routing.station.MODULE)
        routing.owner(name, 'module')
        routing.configure(name, 'module')
    routing.write_json(state_file, state)
    raise
