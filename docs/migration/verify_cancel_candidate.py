"""Compare deployed Cancel and isolated module refund/cancel behavior."""
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
legacy='http://127.0.0.1:18885'
module='http://127.0.0.1:18112'
prefix='/api/v1/cancelservice'
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',body=None):return request(base,path,method,body,test_token())
def order_path(other):return '/api/v1/orderOtherService/orderOther' if other else '/api/v1/orderservice/order'
def order_host(label,other):return module if label=='module' else 'http://127.0.0.1:'+('12032' if other else '12031')
def sample(other):
    key='testOtherOrders' if other else 'testOrders'
    ident=fixture[key][-1]['id']
    status,response=call('http://127.0.0.1:'+('12032' if other else '12031'),order_path(other)+'/'+ident)
    check(('OrderOther' if other else 'Orders')+' source available',status==200 and response['status']==1)
    return response['data']
def create(label,other,source,status):
    order=dict(source);order.pop('id',None)
    order.update(accountId=fixture['userId'],trainNumber='Z1236' if other else 'D1345',
                 status=status,price='250.0')
    response=call(order_host(label,other),order_path(other),'POST',order)
    check(label+' '+('Other' if other else 'standard')+' status '+str(status)+' order created',
          response[0]==200 and response[1]['status']==1 and response[1]['data']['status']==status)
    return response[1]['data']['id']
def current(label,other,ident):
    response=call(order_host(label,other),order_path(other)+'/'+ident)
    return response[0],response[1]['data']['status'] if response[1].get('data') else None

modules=call(module,'/actuator/modulith')[1]
expected=set(json.loads((root/'deployment/migration/.state/hybrid.json').read_text())['modules'])|{'cancel'}
check('candidate has twenty-one business modules',set(modules)==expected)
check('Cancel uses Orders, OrderOther and Inside Payment',
      {edge['target'] for edge in modules['cancel']['dependencies']}==
      {'orders','orderother','insidepayment'})
check('welcome matches',call(legacy,prefix+'/welcome')==call(module,prefix+'/welcome'))
check('unauthenticated welcome status matches',
      request(legacy,prefix+'/welcome')[0]==request(module,prefix+'/welcome')[0])
missing='00000000-0000-0000-0000-000000000000'
check('missing refund matches',call(legacy,prefix+'/cancel/refound/'+missing)==
      call(module,prefix+'/cancel/refound/'+missing))
check('missing cancel matches',call(legacy,prefix+'/cancel/'+missing+'/migration-test')==
      call(module,prefix+'/cancel/'+missing+'/migration-test'))
paid_id=json.loads((root/'ts-modulith/target/evidence/inside-payment-ui.json').read_text())['orderId']
check('existing paid refund matches',call(legacy,prefix+'/cancel/refound/'+paid_id)==
      call(module,prefix+'/cancel/refound/'+paid_id))
standard=sample(False)
other=sample(True)
for label,base in (('legacy',legacy),('module',module)):
    for is_other,source in ((False,standard),(True,other)):
        kind='Other' if is_other else 'standard'
        for state in (0,1,6):
            ident=create(label,is_other,source,state)
            refund=call(base,prefix+'/cancel/refound/'+ident)
            if state==0:
                expected_refund=(200,{'status':1,
                    'msg':'Success, Refound 0' if is_other else 'Success. Refoud 0','data':'0'})
            elif state==1:
                expected_refund=(200,{'status':1,
                    'msg':'Success' if is_other else 'Success. ','data':'200.00'})
            else:
                expected_refund=(200,{'status':0,
                    'msg':'Order Status Cancel Not Permitted' if is_other else
                          'Order Status Cancel Not Permitted, Refound error','data':None})
            check(label+' '+kind+' status '+str(state)+' refund',refund==expected_refund)
            wallet_user='migration-cancel-'+uuid.uuid4().hex
            cancelled=call(base,prefix+'/cancel/'+ident+'/'+wallet_user)
            if state==6:
                check(label+' '+kind+' used order rejects cancellation',
                      cancelled==(200,{'status':0,'msg':'Order Status Cancel Not Permitted','data':None}))
                check(label+' '+kind+' used order unchanged',current(label,is_other,ident)==(200,6))
                continue
            expected_cancel=(200,{'status':1,'msg':'Success.',
                                    'data':None if is_other else 'test not null'})
            check(label+' '+kind+' status '+str(state)+' cancel response',
                  cancelled==expected_cancel)
            check(label+' '+kind+' order cancelled',current(label,is_other,ident)==(200,4))
            check(label+' '+kind+' repeated cancel rejected',
                  call(base,prefix+'/cancel/'+ident+'/'+wallet_user)==
                  (200,{'status':0,'msg':'Order Status Cancel Not Permitted','data':None}))
            account=call(base.replace('18885','18673') if label=='legacy' else module,
                         '/api/v1/inside_pay_service/inside_payment/account')
            check(label+' '+kind+' drawback recorded',account[0]==200 and any(
                  row['userId']==wallet_user and row['balance']=='200.00'
                  for row in account[1]['data']))

output=root/'ts-modulith/target/evidence/cancel-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Cancel candidate comparison passed')
