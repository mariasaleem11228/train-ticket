"""Add User to the shared host after isolated User/Auth contract checks."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=30 or 'user' in existing:
    raise RuntimeError('Expected 30-module Auth checkpoint')
routing.require_gate('user-candidate.json',17)
if any(not (routing.STATE/'backups'/name).exists() for name in
       ('user-cutover-user.archive','user-cutover-auth.archive')):
    raise RuntimeError('User and Auth Mongo backups required')
routing.owner('user','legacy')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/userservice/users/hello')
    if (status,body)!=(200,'Hello'):
        raise RuntimeError('User host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'user'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='user',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'user'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('User host ready; 30 existing routes retained')
