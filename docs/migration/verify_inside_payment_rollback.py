"""Rehearse Inside Payment rollback with synthetic outside-payment orders."""
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
base='http://127.0.0.1:18673'
prefix='/api/v1/inside_pay_service'
order_path='/api/v1/orderservice/order'
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def backend():
    req=urllib.request.Request(base+prefix+'/welcome',
                               headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-InsidePayment-Backend'),response.read().decode()
def pay(stage):
    source=request('http://127.0.0.1:12031',order_path+'/'+fixture['testOrders'][-1]['id'],
                   token=test_token())
    check(stage+' source order available',source[0]==200 and source[1]['status']==1)
    user=str(uuid.uuid4())
    order=dict(source[1]['data']);order.pop('id',None)
    order.update(accountId=user,trainNumber='D1345',status=0,price='50.0')
    status,created=request('http://127.0.0.1:12031',order_path,'POST',order,test_token())
    check(stage+' synthetic order created',status==200 and created['status']==1)
    ident=created['data']['id']
    status,result=request(base,prefix+'/inside_payment','POST',
                          {'userId':user,'orderId':ident,'tripId':'D1345'},test_token())
    check(stage+' payment response',status==200 and result==
          {'status':1,'msg':'Payment Success Pay Success','data':None})
    status,updated=request('http://127.0.0.1:12031',order_path+'/'+ident,token=test_token())
    check(stage+' order paid',status==200 and updated['status']==1 and updated['data']['status']==1)
    return ident
def retained(stage,ident):
    status,records=request(base,prefix+'/inside_payment/payment',token=test_token())
    check(stage+' wallet record retained',status==200 and any(
          row['orderId']==ident and row['type']=='O' for row in records['data']))
    status,records=request('http://127.0.0.1:19001','/api/v1/paymentservice/payment',token=test_token())
    check(stage+' outside Payment record retained',status==200 and any(
          row['orderId']==ident for row in records['data']))

if json.loads(routing.DEFS['insidepayment']['file'].read_text())['mode']!='module':
    raise RuntimeError('Inside Payment must start in module mode')
identity='Welcome to [ InsidePayment Service ] !'
check('module serves Inside Payment',backend()==(200,'module',identity))
try:
    routing.switch('insidepayment','legacy')
    check('legacy serves Inside Payment',backend()==(200,'legacy',identity))
    blocked={'userId':'migration-test-'+uuid.uuid4().hex,'money':'1.0'}
    check('inactive module rejects wallet writes',
          request('http://127.0.0.1:18080',prefix+'/inside_payment/account',
                  'POST',blocked,test_token())[0]==503)
    legacy_id=pay('legacy rollback')
    retained('legacy rollback',legacy_id)
finally:
    if json.loads(routing.DEFS['insidepayment']['file'].read_text())['mode']!='module':
        routing.switch('insidepayment','module')
check('module serves Inside Payment again',backend()==(200,'module',identity))
retained('module after rollback',legacy_id)
module_id=pay('module return')
retained('module return',module_id)
output=root/'ts-modulith/target/evidence/inside-payment-rollback.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Inside Payment rollback rehearsal passed')
