"""Add Food Map to the shared host after its isolated comparison."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=25 or 'foodmap' in existing:raise RuntimeError('Expected 25-module Consign checkpoint')
routing.require_gate('foodmap-candidate.json',15)
if any(not (routing.STATE/'backups'/name).exists() for name in ('foodmap-stores.archive','foodmap-trainfoods.archive')):
    raise RuntimeError('Food Map backups required')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/foodmapservice/trainfoods/welcome')
    if (status,body)!=(200,'Welcome to [ Train Food Service ] !'):
        raise RuntimeError('Food Map host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'foodmap'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='foodmap',image=routing.inspect(routing.station.MODULE)['Image'],modules=[*existing,'foodmap'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Food Map host ready; 25 existing routes retained')
