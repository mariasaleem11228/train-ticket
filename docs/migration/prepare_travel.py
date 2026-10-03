"""Upgrade the shared host to Travel behind the ten existing proxies."""
import json
import hybrid_routing as routing
from http_support import request

EXISTING = ('station','orders','orderother','config','seat','security','train','route','price','basic')
routing.require_gate('travel-comparison.json',42)
if not (routing.STATE/'backups/travel.archive').exists():
    raise RuntimeError('Travel Mongo backup required')
state=json.loads((routing.STATE/'hybrid.json').read_text())
if 'travel' in state['modules']:raise RuntimeError('Travel host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode']!='module' for name in EXISTING):
    raise RuntimeError('All ten existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/travelservice/trips')
    if status!=200 or body.get('status')!=1 or len(body.get('data',[]))!=5:
        raise RuntimeError('Travel host did not read live trips')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(EXISTING)|{'travel'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='travel',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING,'travel'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    raise
finally:
    for name in EXISTING:
        routing.owner(name,'module');routing.configure(name,'module')
print('Travel host prepared; existing ten routes remain on their modules')
