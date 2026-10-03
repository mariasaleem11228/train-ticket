"""Add ConsignPrice to the shared host after an isolated comparison."""
import json
import hybrid_routing as routing
from http_support import request,test_token

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=23 or 'consignprice' in existing:raise RuntimeError('Expected 23-module Assurance checkpoint')
routing.require_gate('consign-price-candidate.json',16)
if not (routing.STATE/'backups/consign-price.archive').exists():raise RuntimeError('ConsignPrice backup required')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/consignpriceservice/welcome',token=test_token())
    if (status,body)!=(200,'Welcome to [ ConsignPrice Service ] !'):raise RuntimeError('ConsignPrice host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'consignprice'}:raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='consignprice',image=routing.inspect(routing.station.MODULE)['Image'],modules=[*existing,'consignprice'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('ConsignPrice host ready; 23 existing routes retained')
