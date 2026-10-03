"""Upgrade the shared host only after the isolated News comparison passes."""
import json
import hybrid_routing as routing
from http_support import request

existing = tuple(json.loads((routing.STATE / 'hybrid.json').read_text())['modules'])
if len(existing) != 37 or 'news' in existing:
    raise RuntimeError('Expected 37-module Voucher checkpoint')
routing.require_gate('news-candidate.json', 6)
for name in existing:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    for name in existing:
        routing.ready(name, routing.station.MODULE)
    status, _ = request('http://127.0.0.1:18080', '/news-service/news')
    if status != 200:
        raise RuntimeError('News host route not ready')
    status, modules = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(modules) != set(existing) | {'news'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE / 'hybrid.json').read_text())
    state.update(stage='news', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'news'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
finally:
    for name in existing:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
print('News host ready; 37 existing routes retained')
