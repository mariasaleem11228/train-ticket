"""Rehearse ConsignPrice rollback without altering the live price configuration."""
import json
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:16110'
prefix='/api/v1/consignpriceservice'
token=test_token()
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def backend():
    req=urllib.request.Request(base+prefix+'/welcome',headers={'Authorization':'Bearer '+token})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-ConsignPrice-Backend'),response.read().decode()
def call(path,host=base,method='GET',body=None):return request(host,prefix+path,method,body,token)

if json.loads(routing.DEFS['consignprice']['file'].read_text())['mode']!='module':
    raise RuntimeError('ConsignPrice must start in module mode')
identity='Welcome to [ ConsignPrice Service ] !'
before=call('/consignprice/config')
quote=call('/consignprice/3/false')
check('module serves ConsignPrice',backend()==(200,'module',identity))
try:
    routing.switch('consignprice','legacy')
    check('legacy serves ConsignPrice',backend()==(200,'legacy',identity))
    check('configuration unchanged on rollback',call('/consignprice/config')==before)
    check('quote unchanged on rollback',call('/consignprice/3/false')==quote)
    check('inactive module rejects configuration writes',
          call('/consignprice',host='http://127.0.0.1:18080',method='POST',body=before[1]['data'])[0]==503)
    check('rejected write preserved configuration',call('/consignprice/config')==before)
finally:
    if json.loads(routing.DEFS['consignprice']['file'].read_text())['mode']!='module':
        routing.switch('consignprice','module')
check('module serves ConsignPrice again',backend()==(200,'module',identity))
check('configuration retained after return',call('/consignprice/config')==before)
check('quote retained after return',call('/consignprice/3/false')==quote)
output=root/'ts-modulith/target/evidence/consign-price-rollback.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ConsignPrice rollback rehearsal passed')
