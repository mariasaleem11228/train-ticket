"""Upgrade the host to include Assurance while retaining the 22 live module routes."""
import json
import hybrid_routing as routing
from http_support import request,test_token

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=22 or 'assurance' in existing:raise RuntimeError('Expected 22-module Rebook checkpoint')
routing.require_gate('assurance-candidate.json',16)
if not (routing.STATE/'backups/assurance.archive').exists():raise RuntimeError('Assurance backup required')
for name in existing:
    routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/assuranceservice/welcome',token=test_token('ROLE_USER'))
    if (status,body)!=(200,'Welcome to [ Assurance Service ] !'):raise RuntimeError('Assurance host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'assurance'}:raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='assurance',image=routing.inspect(routing.station.MODULE)['Image'],modules=[*existing,'assurance'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:
        routing.owner(name,'module');routing.configure(name,'module')
print('Assurance host ready; 22 existing routes retained')
