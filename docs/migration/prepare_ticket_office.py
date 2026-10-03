"""Upgrade the shared host after isolated Ticket Office write comparisons."""
import json

import hybrid_routing as routing
from http_support import request

existing = tuple(json.loads((routing.STATE / 'hybrid.json').read_text())['modules'])
if len(existing) != 38 or 'ticketoffice' in existing:
    raise RuntimeError('Expected 38-module News checkpoint')
routing.require_gate('ticket-office-candidate.json', 17)
if not (routing.STATE / 'backups/ticket-office.archive').exists():
    raise RuntimeError('Ticket Office Mongo backup required')
for name in existing:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080', '/office/')
    if status != 200 or body != 'welcome to ts-ticket-office-service':
        raise RuntimeError('Ticket Office host route not ready')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(existing) | {'ticketoffice'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE / 'hybrid.json').read_text())
    state.update(stage='ticketoffice', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'ticketoffice'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
finally:
    for name in existing:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('Ticket Office host ready; 38 existing routes retained')
