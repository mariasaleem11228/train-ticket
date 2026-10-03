"""Upgrade the shared host after isolated Admin Order contract checks."""
import json
import hybrid_routing as routing
from http_support import request, test_token

existing = tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing) != 34 or 'adminorder' in existing:
    raise RuntimeError('Expected 34-module Admin Travel checkpoint')
routing.require_gate('admin-order-candidate.json',19)
routing.owner('adminorder','legacy')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:
        routing.ready(name,routing.station.MODULE)
    status,body = request('http://127.0.0.1:18080',
                          '/api/v1/adminorderservice/welcome',token=test_token())
    if (status,body) != (200,'Welcome to [Admin Order Service] !'):
        raise RuntimeError('Admin Order host not ready')
    status,modules = request('http://127.0.0.1:18080','/actuator/modulith')
    if status != 200 or set(modules) != set(existing)|{'adminorder'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='adminorder',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'adminorder'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Admin Order host ready; 34 existing routes retained')
