"""Upgrade the shared host to Price behind the existing eight proxies."""
import json
from http_support import request
import hybrid_routing as routing

EXISTING=('station','orders','orderother','config','seat','security','train','route')
routing.require_gate('price-comparison.json',26)
if not (routing.STATE/'backups/price.archive').exists():
    raise RuntimeError('Price Mongo backup required')
state=json.loads((routing.STATE/'hybrid.json').read_text())
if 'price' in state['modules']:raise RuntimeError('Price host already prepared')
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode']!='module' for name in EXISTING):
    raise RuntimeError('All eight existing routes must be in module mode')
for name in EXISTING:
    routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    status,payload=request('http://127.0.0.1:18080','/api/v1/priceservice/prices')
    if status!=200 or payload.get('status')!=1:raise RuntimeError('Price host did not read live catalogue')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(EXISTING)|{'price'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state.update(stage='price',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*EXISTING,'price'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    for name in EXISTING:routing.ready(name,routing.station.MODULE)
    raise
finally:
    for name in EXISTING:
        routing.owner(name,'module');routing.configure(name,'module')
print('Price host prepared; existing eight routes remain on their modules')
