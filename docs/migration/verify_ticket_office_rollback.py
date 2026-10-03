"""Confirm a live module write survives switching to Node and back."""
import json
import urllib.request
from pathlib import Path
from uuid import uuid4

import hybrid_routing as routing

region = {'province': 'Shanghai', 'city': 'Shanghai', 'region': 'Pudong New Area'}
office = {'officeName': 'Migration Rollback ' + uuid4().hex,
          'address': 'Migration test', 'workTime': '09:00-17:00', 'windowNum': 1}
results = []


def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)


def call(path, payload=None):
    request = urllib.request.Request('http://127.0.0.1:16108' + path,
                                     data=None if payload is None else json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.headers.get('X-TicketOffice-Backend'), json.load(response)


def present(mode):
    status, backend, rows = call('/office/getSpecificOffices', region)
    return status == 200 and backend == mode and any(
        item['officeName'] == office['officeName'] for row in rows for item in row['offices'])


if json.loads(routing.DEFS['ticketoffice']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Ticket Office must start in module mode')
created = False
try:
    status, backend, result = call('/office/addOffice', {**region, 'office': office})
    created = status == 200 and result['n'] == 1
    check('module adds synthetic office', created and backend == 'module')
    check('module reads synthetic office', present('module'))
    routing.switch('ticketoffice', 'legacy')
    check('no-reseed Node reads module write', present('legacy'))
    routing.switch('ticketoffice', 'module')
    check('module reads office after rollback rehearsal', present('module'))
finally:
    if json.loads(routing.DEFS['ticketoffice']['file'].read_text())['mode'] != 'module':
        routing.switch('ticketoffice', 'module')
    if created:
        status, backend, result = call('/office/deleteOffice',
                                       {**region, 'officeName': office['officeName']})
        check('synthetic office removed', status == 200 and backend == 'module' and
              result['n'] == 1 and not present('module'))
output = Path(__file__).resolve().parents[2] / 'ts-modulith/target/evidence/ticket-office-rollback.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Ticket Office rollback rehearsal passed')
