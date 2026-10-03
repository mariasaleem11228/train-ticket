"""Compare the deployed Contacts read contract with the read-only module."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
path = '/api/v1/contactservice/contacts'
legacy = 'http://127.0.0.1:12347'
module = 'http://127.0.0.1:18104'
token = test_token()
results = []

def check(label, ok):
    results.append({'step': label, 'passed': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + label, flush=True)
    if not ok:
        raise AssertionError(label)

def canonical(response):
    status, body = response
    if isinstance(body, dict) and isinstance(body.get('data'), list):
        body = dict(body)
        body['data'] = sorted(body['data'], key=lambda item: json.dumps(item, sort_keys=True))
    return status, body

def compare(label, suffix):
    a = canonical(request(legacy, path + suffix, token=token))
    b = canonical(request(module, path + suffix, token=token))
    check(label, a == b)
    return a

check('candidate has fifteen modules',
      set(request(module, '/actuator/modulith')[1]) ==
      {'station','orders','orderother','config','seat','security','train','route',
       'price','basic','travel','travel2','routeplan','travelplan','contacts'})
compare('welcome', '/welcome')
all_contacts = compare('all contacts', '')[1]['data'] or []
for index, contact in enumerate(all_contacts):
    compare(f'contact {index} by id', '/' + contact['id'])
    compare(f'contact {index} by account', '/account/' + contact['accountId'])
compare('unknown contact', '/' + str(uuid.uuid4()))
compare('unknown account', '/account/' + str(uuid.uuid4()))
output = root / 'ts-modulith/target/evidence/contacts-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'Contacts read comparison passed: {len(results)} checks')
