"""Enable verified WaitOrder API and persistence in the shared host."""
import concurrent.futures
import json
import time

import hybrid_routing as routing
from http_support import request,wait_ready

state=json.loads((routing.STATE/'hybrid.json').read_text())
existing=tuple(state['modules'])
if len(existing) not in (43,44) or 'ticketinfo' not in existing or (len(existing)==44 and 'waitorder' not in existing):
    raise RuntimeError('Expected the TicketInfo or WaitOrder checkpoint')
routing.require_gate('wait-order-retry-candidate.json',4)

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

routing.owner('delivery','maintenance')
routing.owner('fooddelivery','maintenance')
routing.owner('waitorder','maintenance')
try:
    routes('maintenance')
    routing.docker(*routing.COMPOSE,'up','-d','wait-order-mysql')
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    wait_ready('http://127.0.0.1:18080','/actuator/health',seconds=180)
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        status,graph=request('http://127.0.0.1:18080','/actuator/modulith')
        if status==200 and set(graph)==set(existing)|{'waitorder'}:break
        time.sleep(3)
    else:raise RuntimeError('Unexpected WaitOrder module graph')
    if {dependency['target'] for dependency in graph['waitorder']['dependencies']}!={'preserve'}:
        raise RuntimeError('WaitOrder must use only Preserve')
    state.update(stage='waitorder',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing] if 'waitorder' in existing else [*existing,'waitorder'])
    routing.write_json(routing.STATE/'hybrid.json',state)
finally:
    routes('module')
    routing.owner('delivery','module')
    routing.owner('fooddelivery','module')
routing.owner('waitorder','module')
print('WaitOrder retry enabled in shared host with stable booking IDs and durable leases')
