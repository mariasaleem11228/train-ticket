"""Add Auth to the shared host after isolated contract and database checks."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=29 or 'auth' in existing:
    raise RuntimeError('Expected 29-module Verification Code checkpoint')
routing.require_gate('auth-candidate.json',22)
if not (routing.STATE/'backups/auth.archive').exists():
    raise RuntimeError('Auth Mongo backup required')
routing.owner('auth','legacy')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/auth/hello')
    if (status,body)!=(200,'hello'):
        raise RuntimeError('Auth host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'auth'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='auth',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'auth'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Auth host ready; 29 existing routes retained')
