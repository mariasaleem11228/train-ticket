"""Upgrade the shared host after isolated Admin User contract checks."""
import json
import hybrid_routing as routing
from http_support import request, test_token

existing = tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing) != 35 or 'adminuser' in existing:
    raise RuntimeError('Expected 35-module Admin Order checkpoint')
routing.require_gate('admin-user-candidate.json',18)
routing.owner('adminuser','legacy')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:
        routing.ready(name,routing.station.MODULE)
    status,body = request('http://127.0.0.1:18080',
                          '/api/v1/adminuserservice/users/welcome',token=test_token())
    if (status,body) != (200,'Welcome to [ AdminUser Service ] !'):
        raise RuntimeError('Admin User host not ready')
    status,modules = request('http://127.0.0.1:18080','/actuator/modulith')
    if status != 200 or set(modules) != set(existing)|{'adminuser'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='adminuser',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'adminuser'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Admin User host ready; 35 existing routes retained')
