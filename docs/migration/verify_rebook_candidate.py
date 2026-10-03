"""Compare deployed Rebook and its isolated Spring Modulith candidate."""
import datetime
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
legacy='http://127.0.0.1:18886'
module='http://127.0.0.1:18113'
prefix='/api/v1/rebookservice'
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=8)).date().isoformat()
token=test_token()
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',body=None):return request(base,path,method,body,token)
def order_path(other):return '/api/v1/orderOtherService/orderOther' if other else '/api/v1/orderservice/order'
def order_host(label,other):return module if label=='module' else 'http://127.0.0.1:'+('12032' if other else '12031')
def source(other):
    key='testOtherOrders' if other else 'testOrders'
    return call(order_host('legacy',other),order_path(other)+'/'+fixture[key][-1]['id'])[1]['data']
def create(label,other,state,price):
    order=dict(source(other));order.pop('id',None)
    order.update(accountId=fixture['userId'],trainNumber='Z1236' if other else 'G1234',
                 status=state,price=price,travelDate=date,
                 contactsDocumentNumber='migration-'+uuid.uuid4().hex)
    result=call(order_host(label,other),order_path(other),'POST',order)
    check(label+' order created',result[0]==200 and result[1]['status']==1)
    return result[1]['data']['id']
def body(ident,old,new):
    return {'orderId':ident,'oldTripId':old,'tripId':new,'seatType':2,'date':date,
            'loginId':'migration-rebook-'+uuid.uuid4().hex}
def current(label,other,ident):
    return call(order_host(label,other),order_path(other)+'/'+ident)[1]

modules=call(module,'/actuator/modulith')[1]
expected=set(json.loads((root/'deployment/migration/.state/hybrid.json').read_text())['modules'])|{'rebook'}
check('candidate has twenty-two business modules',set(modules)==expected)
check('Rebook dependencies are published business modules',
      {e['target'] for e in modules['rebook']['dependencies']}==
      {'orders','orderother','station','travel','travel2','seat','insidepayment'})
check('welcome matches',call(legacy,prefix+'/welcome')==call(module,prefix+'/welcome'))
check('unauthenticated welcome status matches',
      request(legacy,prefix+'/welcome')[0]==request(module,prefix+'/welcome')[0])
missing=body('00000000-0000-0000-0000-000000000000','G1234','G1235')
check('missing order matches',call(legacy,prefix+'/rebook','POST',missing)==
      call(module,prefix+'/rebook','POST',missing))
for label,base in (('legacy',legacy),('module',module)):
    for state in (0,3,6):
        ident=create(label,False,state,'250.0')
        response=call(base,prefix+'/rebook','POST',body(ident,'G1234','G1235'))
        check(label+' rejects status '+str(state),response==
              (200,{'status':0,'msg':'you order not suitable to rebook!','data':None}))
        check(label+' status '+str(state)+' retained',current(label,False,ident)['data']['status']==state)
    for name,other,old,new,old_price,new_price in (
        ('equal',False,'G1234','G1235','250.0','250.0'),
        ('supplement',False,'G1234','G1235','50.0','250.0'),
        ('refund',False,'G1234','G1235','350.0','250.0'),
        ('other equal',True,'Z1236','Z1236','350.0','350.0'),
        ('standard to other',False,'G1234','Z1236','350.0','350.0'),
        ('other to standard',True,'Z1236','G1235','250.0','250.0')):
        ident=create(label,other,1,old_price)
        marker=current(label,other,ident)['data']['contactsDocumentNumber']
        info=body(ident,old,new)
        response=call(base,prefix+'/rebook','POST',info)
        if label=='legacy' and other!=(new.startswith('Z')):
            # Deployed code calls POST on Orders' DELETE endpoint.
            check('legacy '+name+' cross-family defect reproduced',response[0]==500)
            check('legacy '+name+' old order retained',current(label,other,ident)['data']['status']==1)
            continue
        expected_status=2 if name=='supplement' else 1
        check(label+' '+name+' response',response[0]==200 and
              response[1]['status']==expected_status and
              (response[1]['msg']=='Please pay the different money!' if expected_status==2 else
               response[1]['msg']==('Success' if other!= (new.startswith('Z')) else 'Success!')))
        if expected_status==2:
            check(label+' difference quote',response[1]['data']['differenceMoney']=='200.0')
            check(label+' order unchanged before payment',current(label,other,ident)['data']['status']==1)
            response=call(base,prefix+'/rebook/difference','POST',info)
            if label=='legacy':
                # Deployed bytecode sets its HttpHeaders argument to null before
                # the order lookup, so every supplement payment returns HTTP 500.
                check('legacy supplement payment defect reproduced',response[0]==500)
                check('legacy supplement failure leaves order unchanged',
                      current(label,other,ident)['data']['status']==1)
                continue
            check('module repairs supplement payment',response[0]==200 and
                  response[1]['status']==1 and response[1]['msg']=='Success!')
        if other==(new.startswith('Z')):
            updated=current(label,other,ident)
            check(label+' '+name+' order changed',updated['status']==1 and
                  updated['data']['status']==3 and updated['data']['trainNumber']==new and
                  updated['data']['price']==new_price)
            check(label+' '+name+' cannot rebook twice',
                  call(base,prefix+'/rebook','POST',info)==
                  (200,{'status':0,'msg':'you order not suitable to rebook!','data':None}))
        else:
            check(label+' '+name+' old order removed',current(label,other,ident)['status']==0)
            target_other=new.startswith('Z')
            target=call(order_host(label,target_other),order_path(target_other))
            matches=[row for row in target[1].get('data',[]) if
                     row.get('contactsDocumentNumber')==marker and row.get('trainNumber')==new]
            check(label+' '+name+' replacement order retained',target[0]==200 and
                  len(matches)==1 and matches[0]['status']==3 and matches[0]['price']==new_price)

output=root/'ts-modulith/target/evidence/rebook-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Rebook candidate comparison passed')
