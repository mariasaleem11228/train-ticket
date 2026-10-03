"""Rehearse Payment legacy rollback, write ownership, and return to the module."""
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:19001'
path='/api/v1/paymentservice/payment'
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def backend():
    req=urllib.request.Request(base+'/api/v1/paymentservice/welcome',
                               headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-Payment-Backend'),response.read().decode()
def pay(stage):
    body={'orderId':'MIGPAY-'+uuid.uuid4().hex,'userId':'migration-test-'+uuid.uuid4().hex,
          'price':'0.01'}
    status,response=request(base,path,'POST',body,test_token())
    check(stage+' synthetic payment accepted',status==200 and response==
          {'status':1,'msg':'Pay Success','data':None})
    return body
def retained(stage,body):
    status,response=request(base,path,token=test_token())
    check(stage+' payment retained',status==200 and any(
          row['orderId']==body['orderId'] and row['userId']==body['userId']
          for row in response['data']))

if json.loads(routing.DEFS['payment']['file'].read_text())['mode']!='module':
    raise RuntimeError('Payment must start in module mode')
identity='Welcome to [ Payment Service ] !'
check('module serves Payment',backend()==(200,'module',identity))
try:
    routing.switch('payment','legacy')
    check('legacy serves Payment',backend()==(200,'legacy',identity))
    blocked={'orderId':'MIGPAY-'+uuid.uuid4().hex,'userId':'migration-test','price':'0.01'}
    check('inactive Payment module rejects writes',
          request('http://127.0.0.1:18080',path,'POST',blocked,test_token())[0]==503)
    legacy_record=pay('legacy rollback')
    retained('legacy rollback',legacy_record)
finally:
    if json.loads(routing.DEFS['payment']['file'].read_text())['mode']!='module':
        routing.switch('payment','module')
check('module serves Payment again',backend()==(200,'module',identity))
retained('module after rollback',legacy_record)
module_record=pay('module return')
retained('module return',module_record)
output=root/'ts-modulith/target/evidence/payment-rollback.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Payment rollback rehearsal passed')
