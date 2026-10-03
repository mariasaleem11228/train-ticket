"""Verify every backed-up Delivery message reached the live module database."""
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
backup = json.loads((ROOT/'deployment/migration/.state/backups/delivery-queue.json').read_text())
expected = {json.loads(base64.b64decode(payload))['orderId'] for payload in backup['messages_base64']}
owner = json.loads((ROOT/'deployment/migration/.state/ownership/ownership.json').read_text())
if owner.get('delivery') != 'module':
    raise AssertionError('Delivery module does not own queue writes')
with urllib.request.urlopen('http://127.0.0.1:18080/actuator/modulith',timeout=10) as response:
    graph=json.load(response)
if len(graph)<41 or 'delivery' not in graph or graph['delivery']['dependencies']:
    raise AssertionError('Unexpected Delivery module graph')


def queue():
    output=subprocess.check_output(['docker','exec','migration-infra-rabbitmq-1',
        'rabbitmqctl','list_queues','name','messages_ready','messages_unacknowledged','consumers'],text=True)
    for line in output.splitlines():
        fields=line.split('\t')
        if fields[0]=='food_delivery':return tuple(map(int,fields[1:]))
    raise AssertionError('Live delivery queue missing')


def stored():
    output=subprocess.check_output(['docker','exec','station-migration-delivery-mysql-1',
        'mysql','-N','-B','-uroot','-proot','-e',
        'SELECT order_id FROM deliveryservice.delivery'],text=True,stderr=subprocess.DEVNULL)
    return set(output.splitlines())


for attempt in range(90):
    ready, unacked, consumers = queue()
    rows = stored()
    if ready == 0 and unacked == 0 and consumers == 1 and expected <= rows:
        print(f'PASS Delivery module persisted {len(expected)} backed-up messages; queue drained')
        break
    time.sleep(1)
else:
    raise AssertionError(f'Delivery backlog incomplete: queue={(ready,unacked,consumers)} stored={len(rows)} expected={len(expected)}')
