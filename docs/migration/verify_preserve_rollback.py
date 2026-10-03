"""Rehearse a Preserve-only handover and full synthetic booking on each side."""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
path = '/api/v1/preserveservice/welcome'
results = []

def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

def backend():
    req = urllib.request.Request('http://127.0.0.1:14568' + path,
                                 headers={'Authorization': 'Bearer ' + test_token()})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.status, response.headers.get('X-Preserve-Backend'), response.read().decode()

def booking(stage):
    subprocess.run([sys.executable, str(root/'docs/migration/verify_booking.py'), stage],
                   check=True)
    evidence = json.loads((root/f'ts-modulith/target/evidence/booking-{stage}.json').read_text())
    check(stage + ' booking, payment and cancellation', len(evidence) >= 15
          and all(step['passed'] for step in evidence))

if json.loads(routing.DEFS['preserve']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('Preserve must start in module mode')
check('module serves original identity', backend() ==
      (200, 'module', 'Welcome to [ Preserve Service ] !'))
try:
    routing.switch('preserve', 'legacy')
    check('legacy serves original identity', backend() ==
          (200, 'legacy', 'Welcome to [ Preserve Service ] !'))
    check('inactive module rejects booking writes',
          request('http://127.0.0.1:18080', '/api/v1/preserveservice/preserve',
                  'POST', {}, test_token())[0] == 503)
    booking('preserve-rollback')
finally:
    if json.loads(routing.DEFS['preserve']['file'].read_text())['mode'] != 'module':
        routing.switch('preserve', 'module')
check('module serves original identity again', backend() ==
      (200, 'module', 'Welcome to [ Preserve Service ] !'))
booking('preserve-return')
output = root/'ts-modulith/target/evidence/preserve-rollback.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Preserve rollback rehearsal passed')
