"""Upgrade the host to five modules while Seat stays on the deployed service."""
import json
import subprocess
from pathlib import Path
import hybrid_routing as routing
from http_support import request

root = Path(__file__).resolve().parents[2]
names = ('station', 'orders', 'orderother', 'config')
state_file = routing.STATE / 'hybrid.json'
state = json.loads(state_file.read_text())
assert set(state['modules']) == set(names), 'Expected four-module Config checkpoint'
for name in names:
    assert json.loads(routing.DEFS[name]['file'].read_text())['mode'] == 'module'
routing.require_gate('seat-candidate.json', 17)
target = routing.docker('image', 'inspect', 'train-ticket/ts-modulith:seat-candidate', '--format', '{{.Id}}')
previous = routing.inspect(routing.station.MODULE)['Image']
assert previous != target
rollback_overlay = routing.STATE / 'seat-previous-image.yml'
rollback_overlay.write_text('services:\n  modulith:\n    image: ' + previous + '\n')
routing.owner('seat', 'legacy')
for name in names:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in names:
        routing.ready(name, routing.station.MODULE)
    status, welcome = request('http://127.0.0.1:18080', '/api/v1/seatservice/welcome')
    assert status == 200 and welcome == 'Welcome to [ Seat Service ] !'
    status, model = request('http://127.0.0.1:18080', '/actuator/modulith')
    assert status == 200 and set(model) == {'station', 'orders', 'orderother', 'config', 'seat'}
    for name in names:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
    state.update(stage='seat', image=target, modules=[*names, 'seat'])
    routing.write_json(state_file, state)
    routing.write_json(routing.STATE / 'seat-upgrade.json',
                       {'previous_image': previous, 'new_image': target, 'status': 'complete'})
    subprocess.run(['python', str(root/'docs/migration/verify_checkpoint.py')], check=True)
    print('Five-module host ready; Seat remains on its original service')
except Exception:
    routing.docker(*routing.COMPOSE, '-f', str(rollback_overlay), 'up', '-d', 'modulith')
    for name in names:
        routing.ready(name, routing.station.MODULE)
        routing.owner(name, 'module')
        routing.configure(name, 'module')
    routing.write_json(state_file, state)
    raise
