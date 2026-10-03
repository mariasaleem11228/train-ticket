"""Add Verification Code to the shared host after isolated contract checks."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=28 or 'verifycode' in existing:
    raise RuntimeError('Expected 28-module Notification checkpoint')
routing.require_gate('verifycode-candidate.json',16)
routing.owner('verifycode','legacy')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/verifycode/verify/WRONG')
    if (status,body)!=(200,True):
        raise RuntimeError('Verification Code host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'verifycode'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='verifycode',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'verifycode'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Verification Code host ready; 28 existing routes retained')
