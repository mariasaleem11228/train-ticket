"""Add verified Food Delivery to the shared host while preserving existing routes."""
import concurrent.futures
import json
import time

import hybrid_routing as routing
from http_support import request,wait_ready

state=json.loads((routing.STATE/'hybrid.json').read_text())
existing=tuple(state['modules'])
if len(existing)!=41 or 'delivery' not in existing or 'fooddelivery' in existing:
    raise RuntimeError('Expected the 41-module Delivery checkpoint')
routing.require_gate('food-delivery-candidate.json',3)


def reload(name):
    proxy=routing.DEFS[name]['proxy']
    routing.docker('exec',proxy,'nginx','-t')
    routing.docker('exec',proxy,'nginx','-s','reload')


def all_routes(mode):
    for name in existing:
        if name not in routing.DEFS:continue  # Delivery owns a queue, not an HTTP route.
        if mode=='maintenance':routing.owner(name,mode)
        routing.configure(name,mode,reload=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reload,(name for name in existing if name in routing.DEFS)))
    if mode=='module':
        for name in existing:
            if name in routing.DEFS:routing.owner(name,mode)


routing.owner('fooddelivery','maintenance')
routing.owner('delivery','maintenance')
try:
    all_routes('maintenance')
    routing.docker(*routing.COMPOSE,'up','-d','food-delivery-mysql')
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    wait_ready('http://127.0.0.1:18080','/actuator/health',seconds=180)
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        status,graph=request('http://127.0.0.1:18080','/actuator/modulith')
        if status==200 and set(graph)==set(existing)|{'fooddelivery'}:break
        time.sleep(3)
    else:raise RuntimeError('Unexpected Food Delivery module graph')
    if graph['fooddelivery'].get('allowedDependencies')!=['foodmap']:
        raise RuntimeError('Food Delivery must depend only on Food Map')
    state.update(stage='fooddelivery',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'fooddelivery'])
    routing.write_json(routing.STATE/'hybrid.json',state)
finally:
    all_routes('module')
    routing.owner('delivery','module')

routing.owner('fooddelivery','module')
print('Food Delivery enabled; Delivery consumer and 40 existing HTTP routes retained')
