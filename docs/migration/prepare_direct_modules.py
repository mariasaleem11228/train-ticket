"""Upgrade the hybrid host after the isolated direct-module candidate passes."""
import concurrent.futures
import json
import time

import hybrid_routing as routing
from http_support import request, wait_ready

state = json.loads((routing.STATE / 'hybrid.json').read_text())
modules = tuple(state['modules'])
if len(modules) != 45 or 'tripcatalog' not in modules:
    raise RuntimeError('Expected the 45-module Trip Catalog checkpoint')
routing.require_gate('direct-modules-candidate.json', 4)


def reload(name):
    proxy = routing.DEFS[name]['proxy']
    routing.docker('exec', proxy, 'nginx', '-t')
    routing.docker('exec', proxy, 'nginx', '-s', 'reload')


def routes(mode):
    names = [name for name in modules if name in routing.DEFS]
    for name in names:
        if mode == 'maintenance':
            routing.owner(name, mode)
        routing.configure(name, mode, reload=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reload, names))
    if mode == 'module':
        for name in names:
            routing.owner(name, mode)


for name in ('delivery', 'fooddelivery', 'waitorder'):
    routing.owner(name, 'maintenance')
try:
    routes('maintenance')
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    wait_ready('http://127.0.0.1:18080', '/actuator/health', seconds=180)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        status, graph = request('http://127.0.0.1:18080', '/actuator/modulith')
        if status == 200 and set(graph) == set(modules):
            break
        time.sleep(3)
    else:
        raise RuntimeError('Unexpected module graph after direct-module upgrade')
    state.update(stage='direct-modules',
                 image=routing.inspect(routing.station.MODULE)['Image'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
finally:
    routes('module')
    for name in ('delivery', 'fooddelivery', 'waitorder'):
        routing.owner(name, 'module')
print('Direct module calls active in the 45-module host')
