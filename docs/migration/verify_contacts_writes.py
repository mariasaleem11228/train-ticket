"""Exercise Contacts writes in two isolated Mongo databases; live data is untouched."""
import json
import subprocess
import time
import uuid
from pathlib import Path
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
legacy_name = 'station-migration-contacts-legacy-test-1'
module_name = 'station-migration-contacts-module-test-1'
legacy_base = 'http://127.0.0.1:22347'
module_base = 'http://127.0.0.1:18105'
path = '/api/v1/contactservice/contacts'
results = []

def docker(*args):
    return subprocess.check_output(['docker', *args], text=True).strip()

def check(label, ok):
    results.append({'step': label, 'passed': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + label, flush=True)
    if not ok:
        raise AssertionError(label)

def call(base, suffix='', method='GET', body=None):
    return request(base, path + suffix, method, body, test_token())

host = json.loads(docker('inspect', 'station-migration-modulith-1'))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in tuple(env):
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env['CONTACTS_ENABLED'] = 'true'
env['CONTACTS_WRITES_ENABLED'] = 'true'
env['CONTACTS_MONGO_URI'] = 'mongodb://ts-contacts-mongo:27017/contacts_module_migration_test'
env.pop('MODULITH_OWNERSHIP_FILE', None)
env_file = root / 'ts-modulith/target/contacts-write-test.env'
env_file.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
names = docker('ps', '-a', '--format', '{{.Names}}').splitlines()
for name in (legacy_name, module_name):
    if name in names:
        docker('rm', '-f', name)

try:
    docker('run', '-d', '--name', legacy_name, '--network', 'train-ticket_my-network',
           '-p', '127.0.0.1:22347:12347',
           '-e', 'SPRING_DATA_MONGODB_HOST=ts-contacts-mongo',
           '-e', 'SPRING_DATA_MONGODB_DATABASE=contacts_legacy_migration_test',
           '-e', 'JAVA_TOOL_OPTIONS=-XX:+UseSerialGC -Xmx192m',
           'codewisdom/ts-contacts-service:0.2.0')
    docker('run', '-d', '--name', module_name, '--network', 'train-ticket_my-network',
           '-p', '127.0.0.1:18105:18080', '--env-file', str(env_file),
           'train-ticket/ts-modulith:contacts-candidate')
    for base in (legacy_base, module_base):
        for attempt in range(70):
            try:
                if call(base, '/welcome') == (200, 'Welcome to [ Contacts Service ] !'):
                    break
            except OSError:
                pass
            time.sleep(2)
        else:
            raise RuntimeError('Contacts write-test backend not ready: ' + base)

    account = str(uuid.uuid4())
    body = {'accountId': account, 'name': 'Migration Check', 'documentType': 1,
            'documentNumber': 'MIGRATION-TEST-ONLY', 'phoneNumber': '0000000000'}
    created = {}
    for label, base in (('legacy', legacy_base), ('module', module_base)):
        status, result = call(base, method='POST', body=body)
        check(label + ' creates contact', status == 201 and result['status'] == 1
              and result['msg'] == 'Create contacts success'
              and all(result['data'].get(k) == v for k, v in body.items()))
        created[label] = result['data']['id']
        check(label + ' finds contact by account',
              call(base, '/account/' + account)[1]['data'][0]['id'] == created[label])
        check(label + ' rejects duplicate',
              call(base, method='POST', body=body) ==
              (201, {'status': 0, 'msg': 'Contacts already exists', 'data': None}))
        updated = dict(body, id=created[label], name='Migration Updated')
        status, result = call(base, method='PUT', body=updated)
        check(label + ' updates contact', status == 200 and result['status'] == 1
              and result['msg'] == 'Modify success' and result['data']['name'] == 'Migration Updated')
        status, result = call(base, '/' + created[label], method='DELETE')
        check(label + ' deletes contact', status == 200 and result ==
              {'status': 1, 'msg': 'Delete success', 'data': created[label]})
        check(label + ' deleted contact is absent',
              call(base, '/' + created[label])[1] ==
              {'status': 0, 'msg': 'No contacts according to contacts id', 'data': None})
    output = root / 'ts-modulith/target/evidence/contacts-write-comparison.json'
    output.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'Contacts isolated write comparison passed: {len(results)} checks')
finally:
    for name in (legacy_name, module_name):
        if name in docker('ps', '--format', '{{.Names}}').splitlines():
            docker('stop', name)
