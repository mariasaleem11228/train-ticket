"""Add the verified Delivery consumer to the shared host, then enable live ownership."""
import base64
import concurrent.futures
import json
import subprocess
import time

import hybrid_routing as routing
from http_support import request, wait_ready

state = json.loads((routing.STATE / 'hybrid.json').read_text())
existing = tuple(state['modules'])
if len(existing) != 40 or 'delivery' in existing:
    raise RuntimeError('Expected 40-module Avatar checkpoint')
routing.require_gate('delivery-candidate.json', 3)
backup = routing.STATE / 'backups/delivery-queue.json'
saved = json.loads(backup.read_text())['messages_base64']
order_ids = {json.loads(base64.b64decode(payload))['orderId'] for payload in saved}
if len(saved) != 15 or len(order_ids) != 15:
    raise RuntimeError('Live queue backup does not match the 15-message baseline')


def reload(name):
    proxy = routing.DEFS[name]['proxy']
    routing.docker('exec', proxy, 'nginx', '-t')
    routing.docker('exec', proxy, 'nginx', '-s', 'reload')


def all_routes(mode):
    for name in existing:
        if mode == 'maintenance':
            routing.owner(name, mode)
        routing.configure(name, mode, reload=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reload, existing))
    if mode == 'module':
        for name in existing:
            routing.owner(name, mode)


routing.owner('delivery', 'maintenance')
try:
    all_routes('maintenance')
    listed = subprocess.check_output(['docker','exec','migration-infra-rabbitmq-1',
        'rabbitmqctl','list_queues','name','messages_ready','messages_unacknowledged','consumers'],text=True)
    live = next((tuple(map(int,line.split('\t')[1:])) for line in listed.splitlines()
                 if line.startswith('food_delivery\t')), None)
    if live != (len(saved), 0, 0):
        raise RuntimeError(f'Live Delivery queue changed after backup: {live}')
    routing.docker(*routing.COMPOSE, 'up', '-d', 'delivery-mysql')
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    wait_ready('http://127.0.0.1:18080', '/actuator/health', seconds=180)
    status, graph = request('http://127.0.0.1:18080', '/actuator/modulith')
    deadline = time.monotonic() + 180
    while (status != 200 or set(graph) != set(existing) | {'delivery'}) and time.monotonic() < deadline:
        time.sleep(3)
        status, graph = request('http://127.0.0.1:18080', '/actuator/modulith')
    if status != 200 or set(graph) != set(existing) | {'delivery'}:
        raise RuntimeError('Unexpected Delivery module graph')
    if graph['delivery']['dependencies']:
        raise RuntimeError('Delivery should be an independent module')
    state.update(stage='delivery', image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing, 'delivery'])
    routing.write_json(routing.STATE / 'hybrid.json', state)
finally:
    all_routes('module')

# Only this line allows the listener to consume pending live messages.
routing.owner('delivery', 'module')
print('Delivery listener enabled; 40 existing routes retained')
