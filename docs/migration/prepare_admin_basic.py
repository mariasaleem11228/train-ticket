"""Upgrade the shared host after isolated Admin Basic Info checks."""
import json
import hybrid_routing as routing
from http_support import request

existing = tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing) != 31 or 'adminbasic' in existing:
    raise RuntimeError('Expected 31-module User checkpoint')
routing.require_gate('admin-basic-candidate.json',12)
routing.require_gate('admin-basic-writes.json',50)
routing.owner('adminbasic','legacy')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:
        routing.ready(name,routing.station.MODULE)
    status, body = request('http://127.0.0.1:18080',
                           '/api/v1/adminbasicservice/adminbasic/contacts')
    if status != 200 or body.get('status') != 1:
        raise RuntimeError('Admin Basic Info host not ready')
    status, modules = request('http://127.0.0.1:18080','/actuator/modulith')
    if status != 200 or set(modules) != set(existing)|{'adminbasic'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='adminbasic',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'adminbasic'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Admin Basic Info host ready; 31 existing routes retained')
