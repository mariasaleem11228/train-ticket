"""Compare the deployed Admin Basic Info reads and role rules with the candidate."""
import json
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
legacy = 'http://127.0.0.1:18767'
module = 'http://127.0.0.1:18123'
prefix = '/api/v1/adminbasicservice'
results = []

def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

wait_ready(module, '/actuator/health')
for name in ('contacts', 'stations', 'trains', 'configs', 'prices'):
    path = prefix + '/adminbasic/' + name
    old = request(legacy, path)
    new = request(module, path)
    check(name + ' catalogue matches legacy', old == new and old[0] == 200)

for role in (None, 'ROLE_USER', 'ROLE_ADMIN'):
    token = test_token(role) if role else None
    for path in ('/welcome', '/adminbasic/contacts'):
        old = request(legacy, prefix+path, token=token)
        new = request(module, prefix+path, token=token)
        expected = 200 if path != '/welcome' or role == 'ROLE_ADMIN' else 403
        check((role or 'anonymous') + ' ' + path + ' matches legacy',
              old[0] == new[0] == expected and (expected != 200 or old[1] == new[1]))

status, modules = request(module, '/actuator/modulith')
check('32 modules and five declared dependencies', status == 200 and len(modules) == 32
      and {edge['target'] for edge in modules['adminbasic']['dependencies']}
      == {'contacts', 'station', 'train', 'config', 'price'})
output = root / 'ts-modulith/target/evidence/admin-basic-candidate.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Admin Basic Info candidate comparison passed')
