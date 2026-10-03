"""Rehearse Food Map rollback and compare both catalogue APIs."""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
snapshot=root/'ts-modulith/target/evidence/foodmap-rollback-ids.json'
base='http://127.0.0.1:18855'
prefix='/api/v1/foodmapservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def backend():
    with urllib.request.urlopen(base+prefix+'/trainfoods/welcome',timeout=20) as response:
        return response.status,response.headers.get('X-FoodMap-Backend'),response.read().decode()

paths=['/trainfoods','/trainfoods/G1234','/foodstores','/foodstores/shanghai']
if json.loads(routing.DEFS['foodmap']['file'].read_text())['mode']!='module':
    raise RuntimeError('Food Map must start in module mode')
identity='Welcome to [ Train Food Service ] !'
before={path:request(base,prefix+path) for path in paths}
check('module serves Food Map',backend()==(200,'module',identity))
if snapshot.exists():snapshot.unlink()
subprocess.run([sys.executable,str(root/'docs/migration/clean_foodmap_seed.py'),
                'snapshot',str(snapshot)],check=True)
try:
    routing.switch('foodmap','legacy')
    check('legacy serves Food Map',backend()==(200,'legacy',identity))
    subprocess.run([sys.executable,str(root/'docs/migration/clean_foodmap_seed.py'),
                    'clean',str(snapshot)],check=True)
    for path in paths:
        check('legacy retains '+path,request(base,prefix+path)==before[path])
finally:
    if json.loads(routing.DEFS['foodmap']['file'].read_text())['mode']!='module':
        routing.switch('foodmap','module')
    subprocess.run([sys.executable,str(root/'docs/migration/clean_foodmap_seed.py'),
                    'clean',str(snapshot)],check=True)
check('module serves Food Map again',backend()==(200,'module',identity))
for path in paths:
    check('module retains '+path,request(base,prefix+path)==before[path])
output=root/'ts-modulith/target/evidence/foodmap-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Food Map rollback rehearsal passed')
