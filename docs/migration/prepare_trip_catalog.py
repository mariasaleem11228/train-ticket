"""Upgrade the shared host to the verified 45-module Trip Catalog image."""
import concurrent.futures
import json
import time

import hybrid_routing as routing
from http_support import request,wait_ready

state=json.loads((routing.STATE/'hybrid.json').read_text())
existing=tuple(state['modules'])
if len(existing)!=44 or 'waitorder' not in existing or 'tripcatalog' in existing:
    raise RuntimeError('Expected the 44-module WaitOrder checkpoint')
routing.require_gate('trip-catalog-candidate.json',11)
routing.require_gate('trip-catalog-booking-candidate.json',2)

def reload(name):
    proxy=routing.DEFS[name]['proxy']
    routing.docker('exec',proxy,'nginx','-t')
    routing.docker('exec',proxy,'nginx','-s','reload')

def routes(mode):
    names=[name for name in existing if name in routing.DEFS]
    for name in names:
        if mode=='maintenance':routing.owner(name,mode)
        routing.configure(name,mode,reload=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reload,names))
    if mode=='module':
        for name in names:routing.owner(name,mode)

for name in ('delivery','fooddelivery','waitorder'):
    routing.owner(name,'maintenance')
try:
    routes('maintenance')
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    wait_ready('http://127.0.0.1:18080','/actuator/health',seconds=180)
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        status,graph=request('http://127.0.0.1:18080','/actuator/modulith')
        if status==200 and set(graph)==set(existing)|{'tripcatalog'}:break
        time.sleep(3)
    else:raise RuntimeError('Unexpected Trip Catalog module graph')
    assert {d['target'] for d in graph['seat']['dependencies']}=={
        'orders','orderother','config','tripcatalog','route','train'}
    state.update(stage='tripcatalog',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'tripcatalog'])
    routing.write_json(routing.STATE/'hybrid.json',state)
finally:
    routes('module')
    for name in ('delivery','fooddelivery','waitorder'):
        routing.owner(name,'module')
print('Trip Catalog active: Seat reads trip metadata through local module APIs')
