"""Pause, resume, or inspect the live Delivery queue consumer."""
import argparse
import json
import subprocess
import time

import hybrid_routing as routing

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=('pause', 'resume', 'status'))
args = parser.parse_args()


def queue():
    output = subprocess.check_output(
        ['docker', 'exec', 'migration-infra-rabbitmq-1', 'rabbitmqctl',
         'list_queues', 'name', 'messages_ready', 'messages_unacknowledged', 'consumers'],
        text=True)
    for line in output.splitlines():
        fields = line.split('\t')
        if fields[0] == 'food_delivery':
            return tuple(map(int, fields[1:]))
    raise RuntimeError('food_delivery queue missing')


if args.action != 'status':
    routing.owner('delivery', 'maintenance' if args.action == 'pause' else 'module')

target = {'pause': 0, 'resume': 1}.get(args.action)
for attempt in range(15 if target is not None else 1):
    ready, unacked, consumers = queue()
    if target is None or consumers == target:
        break
    time.sleep(1)
else:
    raise RuntimeError(f'Delivery consumer did not reach {target}: {consumers}')

owner = json.loads((routing.STATE / 'ownership/ownership.json').read_text()).get('delivery')
print(f'Delivery owner={owner}; queue ready={ready}, unacknowledged={unacked}, consumers={consumers}')
