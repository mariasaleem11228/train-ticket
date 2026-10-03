"""Rehearse Verification Code route rollback and return to the module."""
import json
import urllib.request
from pathlib import Path

import hybrid_routing as routing

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:15678/api/v1/verifycode'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def probe(mode):
    with urllib.request.urlopen(base+'/generate',timeout=20) as response:
        data=response.read()
        check(mode+' generates CAPTCHA image',response.status==200 and
              response.headers.get('X-VerifyCode-Backend')==mode and
              data.startswith(b'\xff\xd8'))
    with urllib.request.urlopen(base+'/verify/WRONG',timeout=20) as response:
        check(mode+' returns deployed verify response',response.status==200 and
              response.headers.get('X-VerifyCode-Backend')==mode and
              response.read()==b'true')

if json.loads(routing.DEFS['verifycode']['file'].read_text())['mode']!='module':
    raise RuntimeError('Verification Code must start in module mode')
probe('module')
try:
    routing.switch('verifycode','legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['verifycode']['file'].read_text())['mode']!='module':
        routing.switch('verifycode','module')
probe('module')
output=root/'ts-modulith/target/evidence/verifycode-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Verification Code rollback rehearsal passed')
