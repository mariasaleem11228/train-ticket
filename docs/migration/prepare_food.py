"""Add Food to the shared host after its isolated comparison."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=26 or 'food' in existing:raise RuntimeError('Expected 26-module Food Map checkpoint')
routing.require_gate('food-candidate.json',20)
if not (routing.STATE/'backups/food.archive').exists():raise RuntimeError('Food orders backup required')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/foodservice/welcome')
    if (status,body)!=(200,'Welcome to [ Food Service ] !'):
        raise RuntimeError('Food host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'food'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='food',image=routing.inspect(routing.station.MODULE)['Image'],modules=[*existing,'food'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Food host ready; 26 existing routes retained')
