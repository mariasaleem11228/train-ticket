"""Upgrade the shared host to Route behind the existing seven proxies."""
import json
from http_support import request
import hybrid_routing as routing

EXISTING=('station','orders','orderother','config','seat','security','train')
routing.require_gate('route-comparison.json',30)
if not (routing.STATE/'backups/route.archive').exists():
    raise RuntimeError('Route Mongo backup required')
state=json.loads((routing.STATE/'hybrid.json').read_text())
if 'route' in state['modules']:raise RuntimeError('Route host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode']!='module' for name in EXISTING):
    raise RuntimeError('All seven existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    status,payload=request('http://127.0.0.1:18080','/api/v1/routeservice/routes')
    if status!=200 or payload.get('status')!=1:raise RuntimeError('Route host did not read live catalogue')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(EXISTING)|{'route'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='route',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING,'route'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    raise
finally:
    for name in EXISTING:
        routing.owner(name,'module');routing.configure(name,'module')
print('Route host prepared; existing seven routes remain on their modules')
