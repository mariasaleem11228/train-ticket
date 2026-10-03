"""Save pending Delivery messages without acknowledging them."""
import base64
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'deployment/migration/.state/backups/delivery-queue.json'
if TARGET.exists():
    raise RuntimeError('Delivery queue backup already exists; inspect it before replacing')
reader = '''import base64,json,pika
connection=pika.BlockingConnection(pika.ConnectionParameters(
    host="migration-rabbitmq",credentials=pika.PlainCredentials("migration","local-benchmark-only")))
channel=connection.channel()
messages=[]
while True:
    method,props,body=channel.basic_get("food_delivery",auto_ack=False)
    if method is None: break
    messages.append(base64.b64encode(body).decode())
print(json.dumps(messages))
connection.close()  # unacknowledged deliveries are returned to the queue
'''
output = subprocess.check_output(['docker', 'exec', 'delivery-module-candidate',
                                  'python', '-c', reader], text=True)
messages = json.loads(output)
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps({'queue': 'food_delivery', 'messages_base64': messages}, indent=2))
print(f'Saved {len(messages)} Delivery payloads to {TARGET}')
