"""Rehearse Cancel rollback, write ownership, and return using synthetic orders."""
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
base='http://127.0.0.1:18885'
prefix='/api/v1/cancelservice'
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
        return response.status,response.headers.get('X-Cancel-Backend'),response.read().decode()
def cancel(stage):
    status,source=request('http://127.0.0.1:12031',order_path+'/'+fixture['testOrders'][-1]['id'],token=test_token())
    check(stage+' source available',status==200 and source['status']==1)
    order=dict(source['data']);order.pop('id',None)
    order.update(accountId=fixture['userId'],trainNumber='D1345',status=1,price='250.0')
    status,created=request('http://127.0.0.1:12031',order_path,'POST',order,test_token())
    check(stage+' synthetic order created',status==200 and created['status']==1)
    ident=created['data']['id']
    user='migration-cancel-'+uuid.uuid4().hex
    status,result=request(base,prefix+'/cancel/'+ident+'/'+user,token=test_token())
    check(stage+' cancel response',status==200 and result==
          {'status':1,'msg':'Success.','data':'test not null'})
    return ident,user
def retained(stage,ident,user):
    status,order=request('http://127.0.0.1:12031',order_path+'/'+ident,token=test_token())
    check(stage+' order remains cancelled',status==200 and order['status']==1 and order['data']['status']==4)
    status,balances=request('http://127.0.0.1:18673',
                            '/api/v1/inside_pay_service/inside_payment/account',token=test_token())
    check(stage+' drawback retained',status==200 and any(
          row['userId']==user and row['balance']=='200.00' for row in balances['data']))

if json.loads(routing.DEFS['cancel']['file'].read_text())['mode']!='module':
    raise RuntimeError('Cancel must start in module mode')
identity='Welcome to [ Cancel Service ] !'
check('module serves Cancel',backend()==(200,'module',identity))
try:
    routing.switch('cancel','legacy')
    check('legacy serves Cancel',backend()==(200,'legacy',identity))
    check('inactive Cancel module rejects mutating GET',
          request('http://127.0.0.1:18080',prefix+'/cancel/'+
                  '00000000-0000-0000-0000-000000000000/migration-test',
                  token=test_token())[0]==503)
    legacy_id,legacy_user=cancel('legacy rollback')
    retained('legacy rollback',legacy_id,legacy_user)
finally:
    if json.loads(routing.DEFS['cancel']['file'].read_text())['mode']!='module':
        routing.switch('cancel','module')
check('module serves Cancel again',backend()==(200,'module',identity))
retained('module after rollback',legacy_id,legacy_user)
module_id,module_user=cancel('module return')
retained('module return',module_id,module_user)
output=root/'ts-modulith/target/evidence/cancel-rollback.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Cancel rollback rehearsal passed')
