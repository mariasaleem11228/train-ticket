"""Upgrade the shared host to Travel2 behind the eleven existing proxies."""
import json
import hybrid_routing as routing
from http_support import request

EXISTING = ('station','orders','orderother','config','seat','security',
            'train','route','price','basic','travel')
routing.require_gate('travel2-comparison.json', 42)
if not (routing.STATE/'backups/travel2.archive').exists():
    raise RuntimeError('Travel2 Mongo backup required')
state = json.loads((routing.STATE/'hybrid.json').read_text())
if 'travel2' in state['modules']:
    raise RuntimeError('Travel2 host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
       for name in EXISTING):
    raise RuntimeError('All eleven existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080', '/api/v1/travel2service/trips')
    if status != 200 or body.get('status') != 1 or len(body.get('data', [])) != 5:
        raise RuntimeError('Travel2 host did not read live trips')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(EXISTING) | {'travel2'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='travel2', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING, 'travel2'])
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
print('Travel2 host prepared; existing eleven routes remain on their modules')
