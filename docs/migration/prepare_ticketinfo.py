"""Enable TicketInfo after isolated legacy parity checks."""
import concurrent.futures
import json
import time

import hybrid_routing as routing
from http_support import request,wait_ready

state=json.loads((routing.STATE/'hybrid.json').read_text())
existing=tuple(state['modules'])
if len(existing)!=42 or 'fooddelivery' not in existing or 'ticketinfo' in existing:
    raise RuntimeError('Expected the 42-module Food Delivery checkpoint')
routing.require_gate('ticketinfo-candidate.json',4)


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
try:
    routes('maintenance')
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    wait_ready('http://127.0.0.1:18080','/actuator/health',seconds=180)
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        status,graph=request('http://127.0.0.1:18080','/actuator/modulith')
        if status==200 and set(graph)==set(existing)|{'ticketinfo'}:break
        time.sleep(3)
    else:raise RuntimeError('Unexpected TicketInfo module graph')
    if {d['target'] for d in graph['ticketinfo']['dependencies']}!={'basic','station'}:
        raise RuntimeError('Unexpected TicketInfo dependencies')
    state.update(stage='ticketinfo',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'ticketinfo'])
    routing.write_json(routing.STATE/'hybrid.json',state)
finally:
    routes('module')
    routing.owner('delivery','module')
    routing.owner('fooddelivery','module')
print('TicketInfo enabled in shared host; legacy comparison container retained')
