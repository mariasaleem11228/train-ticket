"""Rehearse Notification-only rollback without sending live mail."""
import json
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:17853'
prefix='/api/v1/notifyservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def backend():
    with urllib.request.urlopen(base+prefix+'/welcome',timeout=20) as response:
        return response.status,response.headers.get('X-Notification-Backend')

def consumers():
    output=subprocess.check_output(['docker','exec','migration-infra-rabbitmq-1',
                                    'rabbitmqctl','list_queues','-q','name','consumers'],text=True)
    return int(dict(line.split('\t') for line in output.splitlines()[1:])['email'])

def one_consumer():
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if consumers()==1:return True
        time.sleep(1)
    return False

if json.loads(routing.DEFS['notification']['file'].read_text())['mode']!='module':
    raise RuntimeError('Notification must start in module mode')
check('module serves Notification',backend()==(200,'module'))
check('one live email consumer',one_consumer())
try:
    routing.switch('notification','legacy')
    check('legacy serves Notification',backend()==(200,'legacy'))
    check('one consumer after rollback',one_consumer())
    sample={'email':'rollback-'+uuid.uuid4().hex+'@example.test','username':'Rollback'}
    check('inactive module refuses email',
          request('http://127.0.0.1:18080',prefix+'/notification/preserve_success',
                  'POST',sample)[0]==503)
finally:
    if json.loads(routing.DEFS['notification']['file'].read_text())['mode']!='module':
        routing.switch('notification','module')
check('module serves Notification again',backend()==(200,'module'))
check('one consumer after return',one_consumer())
output=root/'ts-modulith/target/evidence/notification-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Notification rollback rehearsal passed')
