"""Verify isolated Delivery queue persistence without consuming the live backlog."""
import json
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RABBIT = 'migration-infra-rabbitmq-1'
DB = 'station-migration-delivery-mysql-1'
CANDIDATE = 'delivery-module-candidate'


def queues():
    lines = subprocess.check_output(['docker', 'exec', RABBIT, 'rabbitmqctl', 'list_queues',
                                     'name', 'messages_ready', 'consumers'], text=True).splitlines()
    return {parts[0]: (int(parts[1]), int(parts[2])) for line in lines
            if len(parts := line.split('\t')) == 3 and parts[1].isdigit()}


def rows(order_id):
    sql = ("SELECT CONCAT(order_id,'|',food_name,'|',store_name,'|',station_name) "
           f"FROM delivery_candidate.delivery WHERE order_id='{order_id}'")
    output = subprocess.check_output(['docker', 'exec', DB, 'mysql', '-N', '-B', '-uroot', '-proot',
                                      '-e', sql], text=True, stderr=subprocess.DEVNULL)
    return output.splitlines()


before = queues()
if before.get('food_delivery_candidate', (0, 0))[1] != 1:
    raise AssertionError('Expected one isolated Delivery consumer')
with urllib.request.urlopen('http://127.0.0.1:18141/actuator/modulith', timeout=10) as response:
    graph = json.load(response)
if len(graph) != 41 or graph['delivery']['dependencies']:
    raise AssertionError('Delivery module graph differs')

order_id = str(uuid.uuid4())
message = {'orderId': order_id, 'foodName': 'Migration Soup',
           'storeName': 'Migration Store', 'stationName': 'Shang Hai'}
publisher = '''import json,pika,sys
payload=sys.stdin.read()
connection=pika.BlockingConnection(pika.ConnectionParameters(
    host="migration-rabbitmq",credentials=pika.PlainCredentials("migration","local-benchmark-only")))
channel=connection.channel()
for _ in range(2):
    channel.basic_publish(exchange="",routing_key="food_delivery_candidate",body=payload,
        properties=pika.BasicProperties(delivery_mode=2))
connection.close()
'''
subprocess.run(['docker', 'exec', '-i', CANDIDATE, 'python', '-c', publisher],
               input=json.dumps(message), text=True, check=True)
for attempt in range(40):
    found = rows(order_id)
    if found:
        break
    time.sleep(1)
else:
    raise AssertionError('Delivery message was not persisted')
expected = order_id + '|Migration Soup|Migration Store|Shang Hai'
if found != [expected]:
    raise AssertionError(f'Delivery persistence or duplicate handling differs: {found}')
after = queues()
if after['food_delivery_candidate'][0] != 0 or after['food_delivery'][0] != before['food_delivery'][0]:
    raise AssertionError('Candidate queue did not drain or live queue changed')
evidence = ROOT / 'ts-modulith/target/evidence/delivery-candidate.json'
evidence.parent.mkdir(parents=True, exist_ok=True)
evidence.write_text(json.dumps([
    {'step': 'Delivery is the 41st independent module', 'passed': True},
    {'step': 'candidate queue duplicate persisted once', 'passed': True},
    {'step': 'live queue unchanged', 'passed': True},
], indent=2))
print('PASS Delivery module, duplicate persistence, isolated queue, and unchanged live backlog')
