"""Compare deployed Inside Payment and isolated module across wallet and order paths."""
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
legacy='http://127.0.0.1:18673'
module='http://127.0.0.1:18111'
prefix='/api/v1/inside_pay_service'
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',body=None):return request(base,path,method,body,test_token())
def order_host(label,other):return module if label=='module' else 'http://127.0.0.1:'+('12032' if other else '12031')
def order_path(other):return '/api/v1/orderOtherService/orderOther' if other else '/api/v1/orderservice/order'
def source_order(other):
    key='testOtherOrders' if other else 'testOrders'
    sample=fixture[key][-1]['id']
    status,response=call('http://127.0.0.1:'+('12032' if other else '12031'),order_path(other)+'/'+sample)
    check(('OrderOther' if other else 'Orders')+' sample available',status==200 and response['status']==1)
    return response['data']
def make_order(label,other,sample,user):
    order=dict(sample);order.pop('id',None)
    order['accountId']=user
    order['trainNumber']='Z' if other else 'D1345'
    order['status']=0
    order['price']='50.0'
    host=order_host(label,other)
    status,response=call(host,order_path(other),'POST',order)
    check(label+' '+('Other' if other else 'standard')+' synthetic order created',
          status==200 and response['status']==1 and response['data']['status']==0)
    return response['data']['id']
def order_state(label,other,ident):
    status,response=call(order_host(label,other),order_path(other)+'/'+ident)
    return status,response['data']['status'] if response.get('data') else None
def wallet_payment(label,ident):
    status,response=call(legacy if label=='legacy' else module,prefix+'/inside_payment/payment')
    matches=[row for row in response.get('data') or [] if row['orderId']==ident]
    return status,matches
def outside_payment(label,ident):
    status,response=call('http://127.0.0.1:19001' if label=='legacy' else module,
                         '/api/v1/paymentservice/payment')
    return status,[row for row in response.get('data') or [] if row['orderId']==ident]

modules=call(module,'/actuator/modulith')[1]
expected=set(json.loads((root/'deployment/migration/.state/hybrid.json').read_text())['modules'])|{'insidepayment'}
check('candidate has twenty business modules',set(modules)==expected)
check('Inside Payment uses Orders, OrderOther and Payment',
      {edge['target'] for edge in modules['insidepayment']['dependencies']}==
      {'orders','orderother','payment'})
check('welcome matches',call(legacy,prefix+'/welcome')==call(module,prefix+'/welcome'))
for path in ('/inside_payment/payment','/inside_payment/account','/inside_payment/money'):
    old=call(legacy,prefix+path);new=call(module,prefix+path)
    if path.endswith('/payment'):
        passed=old[0]==new[0]==200 and old[1]['status']==new[1]['status'] and old[1]['msg']==new[1]['msg'] and sorted(old[1]['data'],key=lambda x:x['id'])==sorted(new[1]['data'],key=lambda x:x['id'])
    elif path.endswith('/account'):
        passed=old[0]==new[0]==200 and old[1]['status']==new[1]['status'] and old[1]['msg']==new[1]['msg'] and sorted(old[1]['data'],key=lambda x:x['userId'])==sorted(new[1]['data'],key=lambda x:x['userId'])
    else:passed=old==new
    check('existing '+path.rsplit('/',1)[-1]+' query matches',passed)
check('unauthenticated read status matches',
      request(legacy,prefix+'/inside_payment/payment')[0]==
      request(module,prefix+'/inside_payment/payment')[0])

sample_standard=source_order(False)
sample_other=source_order(True)
for label,base in (('legacy',legacy),('module',module)):
    user=str(uuid.uuid4())
    account={'userId':user,'money':'1000.0'}
    created=call(base,prefix+'/inside_payment/account','POST',account)
    check(label+' wallet account created',created==(200,{'status':1,'msg':'Create Account Success','data':None}))
    check(label+' duplicate account rejected',
          call(base,prefix+'/inside_payment/account','POST',account)==
          (200,{'status':0,'msg':'Create Account Failed, Account already Exists','data':None}))
    added=call(base,prefix+'/inside_payment/'+user+'/5.0')
    check(label+' addMoney accepted',added==(200,{'status':1,'msg':'Add Money Success','data':None}))
    balance=call(base,prefix+'/inside_payment/account')
    check(label+' wallet balance updated',balance[0]==200 and any(
          row['userId']==user and row['balance']=='1005.0' for row in balance[1]['data']))

    wallet_id=make_order(label,False,sample_standard,user)
    paid=call(base,prefix+'/inside_payment','POST',
              {'userId':user,'orderId':wallet_id,'tripId':'D1345'})
    check(label+' wallet payment response',paid==(200,{'status':1,'msg':'Payment Success','data':None}))
    check(label+' wallet payment updates order',order_state(label,False,wallet_id)==(200,1))
    status,rows=wallet_payment(label,wallet_id)
    check(label+' wallet payment retained',status==200 and len(rows)==1 and rows[0]['type']=='P')

    external_user=str(uuid.uuid4())
    external_id=make_order(label,True,sample_other,external_user)
    paid=call(base,prefix+'/inside_payment','POST',
              {'userId':external_user,'orderId':external_id,'tripId':'Z1236'})
    check(label+' outside payment response',paid==(200,{'status':1,
          'msg':'Payment Success Pay Success','data':None}))
    check(label+' outside payment updates Other order',order_state(label,True,external_id)==(200,1))
    status,rows=wallet_payment(label,external_id)
    check(label+' outside wallet record retained',status==200 and len(rows)==1 and rows[0]['type']=='O')
    status,rows=outside_payment(label,external_id)
    check(label+' outside Payment record retained',status==200 and len(rows)==1)
    check(label+' duplicate payment blocked by order status',
          call(base,prefix+'/inside_payment','POST',
               {'userId':external_user,'orderId':external_id,'tripId':'Z1236'})==
          (200,{'status':0,'msg':'Error. Order status Not allowed to Pay.','data':None}))

    check(label+' drawback response',call(base,prefix+'/inside_payment/drawback/'+user+'/2.0')==
          (200,{'status':1,'msg':'Draw Back Money Success','data':None}))
    check(label+' difference response',call(base,prefix+'/inside_payment/difference','POST',
          {'userId':user,'orderId':'MIGDIFF-'+uuid.uuid4().hex,'price':'1.0'})==
          (200,{'status':1,'msg':'Pay Difference Success','data':None}))

    # The current Order List JavaScript submits orderId and tripId without userId.
    ui_id=make_order(label,False,sample_standard,str(uuid.uuid4()))
    check(label+' browser-shaped payment response',
          call(base,prefix+'/inside_payment','POST',{'orderId':ui_id,'tripId':'D1345'})==
          (200,{'status':1,'msg':'Payment Success Pay Success','data':None}))
    check(label+' browser-shaped order paid',order_state(label,False,ui_id)==(200,1))
    status,rows=wallet_payment(label,ui_id)
    check(label+' browser-shaped wallet record',status==200 and len(rows)==1 and
          rows[0]['type']=='O' and rows[0]['userId']=='')
    status,rows=outside_payment(label,ui_id)
    check(label+' browser-shaped outside Payment record',status==200 and len(rows)==1 and
          rows[0]['userId']=='')

output=root/'ts-modulith/target/evidence/inside-payment-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Inside Payment candidate comparison passed')
