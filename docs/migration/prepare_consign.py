"""Add Consign to the shared host after its isolated comparison."""
import json
import hybrid_routing as routing
from http_support import request,test_token

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=24 or 'consign' in existing:raise RuntimeError('Expected 24-module ConsignPrice checkpoint')
routing.require_gate('consign-candidate.json',20)
if not (routing.STATE/'backups/consign.archive').exists():raise RuntimeError('Consign backup required')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/consignservice/welcome',token=test_token())
    if (status,body)!=(200,'Welcome to [ Consign Service ] !'):raise RuntimeError('Consign host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'consign'}:raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='consign',image=routing.inspect(routing.station.MODULE)['Image'],modules=[*existing,'consign'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Consign host ready; 24 existing routes retained')
