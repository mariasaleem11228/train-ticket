"""Upgrade the shared host with Contacts behind fourteen existing proxies."""
import json
import hybrid_routing as routing
from http_support import request, test_token

existing = ('station','orders','orderother','config','seat','security','train','route',
            'price','basic','travel','travel2','routeplan','travelplan')
routing.require_gate('contacts-comparison.json', 11)
routing.require_gate('contacts-write-comparison.json', 12)
if not (routing.STATE/'backups/contacts.archive').exists():
    raise RuntimeError('Contacts backup required')
state = json.loads((routing.STATE/'hybrid.json').read_text())
if 'contacts' in state['modules']:
    raise RuntimeError('Contacts host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
       for name in existing):
    raise RuntimeError('All fourteen existing routes must be in module mode')
for name in existing:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080',
                           '/api/v1/contactservice/contacts', token=test_token())
    if status != 200 or body.get('status') != 1:
        raise RuntimeError('Contacts host not ready')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(existing) | {'contacts'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='contacts', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'contacts'])
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
print('Contacts host prepared; existing fourteen routes remain on their modules')
