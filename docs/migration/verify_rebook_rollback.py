"""Rehearse independent Rebook rollback and return with synthetic orders."""
import datetime
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
base='http://127.0.0.1:18886'
prefix='/api/v1/rebookservice'
order_path='/api/v1/orderservice/order'
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=8)).date().isoformat()
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def backend():
    req=urllib.request.Request(base+prefix+'/welcome',
                               headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-Rebook-Backend'),response.read().decode()
def rebook(stage):
    status,source=request('http://127.0.0.1:12031',
                          order_path+'/'+fixture['testOrders'][-1]['id'],token=test_token())
    check(stage+' source available',status==200 and source['status']==1)
    order=dict(source['data']);order.pop('id',None)
    order.update(accountId=fixture['userId'],trainNumber='G1234',status=1,
                 price='250.0',travelDate=date,
                 contactsDocumentNumber='migration-'+uuid.uuid4().hex)
    status,created=request('http://127.0.0.1:12031',order_path,'POST',order,test_token())
    check(stage+' synthetic order created',status==200 and created['status']==1)
    ident=created['data']['id']
    info={'orderId':ident,'oldTripId':'G1234','tripId':'G1235','seatType':2,
          'date':date,'loginId':'migration-rebook-'+uuid.uuid4().hex}
    status,result=request(base,prefix+'/rebook','POST',info,test_token())
    check(stage+' rebook response',status==200 and result['status']==1 and
          result['msg']=='Success!')
    return ident
def retained(stage,ident):
    status,order=request('http://127.0.0.1:12031',order_path+'/'+ident,token=test_token())
    check(stage+' order remains changed',status==200 and order['status']==1 and
          order['data']['status']==3 and order['data']['trainNumber']=='G1235')

if json.loads(routing.DEFS['rebook']['file'].read_text())['mode']!='module':
    raise RuntimeError('Rebook must start in module mode')
identity='Welcome to [ Rebook Service ] !'
check('module serves Rebook',backend()==(200,'module',identity))
try:
    routing.switch('rebook','legacy')
    check('legacy serves Rebook',backend()==(200,'legacy',identity))
    check('inactive Rebook module rejects writes',
          request('http://127.0.0.1:18080',prefix+'/rebook','POST',
                  {'orderId':'00000000-0000-0000-0000-000000000000',
                   'oldTripId':'G1234','tripId':'G1235','seatType':2,'date':date},
                  token=test_token())[0]==503)
    legacy_id=rebook('legacy rollback')
    retained('legacy rollback',legacy_id)
finally:
    if json.loads(routing.DEFS['rebook']['file'].read_text())['mode']!='module':
        routing.switch('rebook','module')
check('module serves Rebook again',backend()==(200,'module',identity))
retained('module after rollback',legacy_id)
module_id=rebook('module return')
retained('module return',module_id)
output=root/'ts-modulith/target/evidence/rebook-rollback.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Rebook rollback rehearsal passed')
