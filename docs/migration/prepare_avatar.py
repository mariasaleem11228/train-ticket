"""Upgrade the shared host after Avatar image-contract comparison passes."""
import json
import hybrid_routing as routing
from http_support import request

existing = tuple(json.loads((routing.STATE / 'hybrid.json').read_text())['modules'])
if len(existing) != 39 or 'avatar' in existing:
    raise RuntimeError('Expected 39-module Ticket Office checkpoint')
routing.require_gate('avatar-candidate.json', 3)
status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
if status == 200 and set(modules) == set(existing) | {'avatar'}:
    state = json.loads((routing.STATE / 'hybrid.json').read_text())
    state.update(stage='avatar', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'avatar'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
    print('Avatar host already ready; 39 existing routes retained')
    raise SystemExit(0)
for name in existing:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(existing) | {'avatar'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE / 'hybrid.json').read_text())
    state.update(stage='avatar', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'avatar'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
finally:
    for name in existing:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('Avatar host ready; 39 existing routes retained')
