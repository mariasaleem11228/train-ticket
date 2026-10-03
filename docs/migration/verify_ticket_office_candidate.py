"""Compare deployed Node and Java Ticket Office on isolated Mongo copies."""
import json
import urllib.request
from pathlib import Path

from http_support import request, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:26108'
new = 'http://127.0.0.1:18130'
results = []


def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)


def call(base, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read()
        try:
            body = json.loads(raw)
        except ValueError:
            body = raw.decode()
        return response.status, response.headers.get('Content-Type'), response.headers.get('Encodeing'), body


def same(label, path, payload=None):
    before = call(old, path, payload)
    after = call(new, path, payload)
    check(label, before[0] == after[0] == 200 and before[2:] == after[2:] and
          before[1].replace(' ', '').lower() == after[1].replace(' ', '').lower())
    return after[3]


wait_ready(new, '/actuator/health')
status, modules = request(new, '/actuator/modulith')
check('39 Spring Modulith business modules', status == 200 and len(modules) == 39 and 'ticketoffice' in modules)
check('Ticket Office has no module dependencies', modules['ticketoffice']['dependencies'] == [])
same('welcome matches deployed Node', '/office/')
same('region list matches deployed Node', '/office/getRegionList')
baseline = same('all offices match deployed Node', '/office/getAll')
check('baseline contains four regions', len(baseline) == 4)
region = {'province': 'Shanghai', 'city': 'Shanghai', 'region': 'Pudong New Area'}
same('specific region matches deployed Node', '/office/getSpecificOffices', region)
same('missing region returns empty list', '/office/getSpecificOffices',
     {'province': 'No such province', 'city': 'None', 'region': 'None'})
office = {'officeName': 'Migration Test Office', 'address': 'Test Address',
          'workTime': '09:00-17:00', 'windowNum': 2}
same('add office matches deployed Node', '/office/addOffice', {**region, 'office': office})
after_add = same('added office appears in both copies', '/office/getSpecificOffices', region)
check('added office persisted', any(o['officeName'] == office['officeName'] for o in after_add[0]['offices']))
updated = dict(office, officeName='Migration Updated Office', address='Updated Address')
same('update office matches deployed Node', '/office/updateOffice',
     {**region, 'oldOfficeName': office['officeName'], 'newOffice': updated})
after_update = same('updated office appears in both copies', '/office/getSpecificOffices', region)
check('updated office persisted', any(o['officeName'] == updated['officeName'] and
                                       o['address'] == updated['address'] for o in after_update[0]['offices']))
same('delete office matches deployed Node', '/office/deleteOffice',
     {**region, 'officeName': updated['officeName']})
same('original region restored', '/office/getSpecificOffices', region)
same('all offices restored', '/office/getAll')
output = root / 'ts-modulith/target/evidence/ticket-office-candidate.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Ticket Office candidate comparison passed')
