"""Upgrade the shared host with Preserve behind fifteen existing proxies."""
import json
import hybrid_routing as routing
from http_support import request, test_token

existing = ('station','orders','orderother','config','seat','security','train','route',
            'price','basic','travel','travel2','routeplan','travelplan','contacts')
routing.require_gate('preserve-candidate.json', 7)
routing.require_gate('booking-preserve-baseline.json', 15)
if not (routing.STATE/'backups/preserve-orders.archive').exists():
    raise RuntimeError('Orders backup required for Preserve cutover')
state = json.loads((routing.STATE/'hybrid.json').read_text())
if 'preserve' in state['modules']:
    raise RuntimeError('Preserve host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
       for name in existing):
    raise RuntimeError('All fifteen existing routes must be in module mode')
for name in existing:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080',
                           '/api/v1/preserveservice/welcome', token=test_token())
    if status != 200 or body != 'Welcome to [ Preserve Service ] !':
        raise RuntimeError('Preserve host not ready')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(existing) | {'preserve'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='preserve', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'preserve'])
    routing.write_json(routing.STATE/'hybrid.json', state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2], 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    raise
finally:
    for name in existing:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('Preserve host prepared; existing fifteen routes remain on their modules')
