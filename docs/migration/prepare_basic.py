"""Upgrade the shared host to Basic while existing nine service routes stay intact."""
import json
import hybrid_routing as routing
from http_support import request

EXISTING = ('station', 'orders', 'orderother', 'config', 'seat',
            'security', 'train', 'route', 'price')
routing.require_gate('basic-comparison.json', 26)
state = json.loads((routing.STATE / 'hybrid.json').read_text())
if 'basic' in state['modules']:
    raise RuntimeError('Basic host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
       for name in EXISTING):
    raise RuntimeError('All nine existing routes must be in module mode')

for name in EXISTING:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080', '/api/v1/basicservice/welcome')
    if status != 200 or body != 'Welcome to [ Basic Service ] !':
        raise RuntimeError('Basic host did not respond')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(EXISTING) | {'basic'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='basic', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING, 'basic'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
except Exception:
    # Remove only the Basic overlay to restore the previously serving image.
    routing.docker(*routing.COMPOSE[:-2], 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    raise
finally:
    for name in EXISTING:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('Basic host prepared; existing nine routes remain on their modules')
