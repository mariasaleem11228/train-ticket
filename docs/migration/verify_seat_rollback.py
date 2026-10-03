"""Rehearse Seat-only rollback without changing booking or order data."""
import datetime
import json
import subprocess
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
PATH = '/api/v1/seatservice/seats/left_tickets'
body = {'travelDate': (datetime.datetime.now(datetime.timezone.utc) +
        datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        'trainNumber': 'G1234', 'startStation': 'nanjing',
        'destStation': 'shanghai', 'seatType': 2}
checks = []


def check(label, condition):
    checks.append({'step': label, 'passed': bool(condition)})
    print(('PASS' if condition else 'FAIL') + ' ' + label, flush=True)
    if not condition:
        raise AssertionError(label)


def left():
    return request('http://127.0.0.1:18898', PATH, 'POST', body, test_token())


assert json.loads(routing.DEFS['seat']['file'].read_text())['mode'] == 'module'
module_before = left()
check('module availability responds', module_before[0] == 200 and module_before[1]['status'] == 1)
try:
    routing.switch('seat', 'legacy')
    subprocess.run(['python', str(ROOT/'docs/migration/verify_checkpoint.py')], check=True)
    check('legacy availability matches module', left() == module_before)
finally:
    if json.loads(routing.DEFS['seat']['file'].read_text())['mode'] != 'module':
        routing.switch('seat', 'module')

subprocess.run(['python', str(ROOT/'docs/migration/verify_checkpoint.py')], check=True)
check('module availability restored', left() == module_before)
output = ROOT / 'ts-modulith/target/evidence/seat-rollback.json'
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Seat rollback rehearsal passed')
