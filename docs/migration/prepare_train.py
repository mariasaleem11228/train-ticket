"""Upgrade the shared host to the Train candidate behind existing six proxies."""
import json
from http_support import request
import hybrid_routing as routing

EXISTING = ('station', 'orders', 'orderother', 'config', 'seat', 'security')
routing.require_gate('train-comparison.json', 22)
if not (routing.STATE/'backups/train.archive').exists():
    raise RuntimeError('Train Mongo backup required')
state = json.loads((routing.STATE/'hybrid.json').read_text())
if 'train' in state['modules']:
    raise RuntimeError('Train host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module' for name in EXISTING):
    raise RuntimeError('All six existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    status, payload = request('http://127.0.0.1:18080', '/api/v1/trainservice/trains')
    if status != 200 or payload.get('status') != 1:
        raise RuntimeError('Train host did not read the live catalogue')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(EXISTING) | {'train'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='train', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING, 'train'])
    routing.write_json(routing.STATE/'hybrid.json', state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2], 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    raise
finally:
    for name in EXISTING:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('Train host prepared; existing six routes remain on their modules')
