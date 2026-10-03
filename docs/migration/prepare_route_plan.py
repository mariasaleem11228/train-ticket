"""Upgrade the shared host with Route Plan behind twelve existing proxies."""
import json
import hybrid_routing as routing
from http_support import request

EXISTING = ('station','orders','orderother','config','seat','security',
            'train','route','price','basic','travel','travel2')
routing.require_gate('route-plan-comparison.json', 22)
state = json.loads((routing.STATE/'hybrid.json').read_text())
if 'routeplan' in state['modules']:
    raise RuntimeError('Route Plan host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
       for name in EXISTING):
    raise RuntimeError('All twelve existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in EXISTING:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080', '/api/v1/routeplanservice/welcome')
    if status != 200 or body != 'Welcome to [ RoutePlan Service ] !':
        raise RuntimeError('Route Plan host not ready')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(EXISTING) | {'routeplan'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='routeplan', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING, 'routeplan'])
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
print('Route Plan host prepared; existing twelve routes remain on their modules')
