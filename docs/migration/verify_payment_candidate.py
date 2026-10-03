"""Compare deployed Payment with an isolated Spring Modulith candidate."""
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:19001'
candidate='http://127.0.0.1:18110'
path='/api/v1/paymentservice/payment'
results=[]
def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

modules=request(candidate,'/actuator/modulith')[1]
expected=set(json.loads((root/'deployment/migration/.state/hybrid.json').read_text())['modules'])|{'payment'}
check('candidate has nineteen business modules',set(modules)==expected)
check('Payment has no module dependencies',modules['payment']['dependencies']==[])
check('welcome matches deployed Payment',request(legacy,'/api/v1/paymentservice/welcome',token=test_token())==
      request(candidate,'/api/v1/paymentservice/welcome',token=test_token()))
old=request(legacy,path,token=test_token())
new=request(candidate,path,token=test_token())
check('existing query status and message match',old[0]==new[0]==200 and
      (old[1]['status'],old[1]['msg'])==(new[1]['status'],new[1]['msg']))
check('existing payment records match',
      sorted(old[1]['data'],key=lambda x:x['id'])==sorted(new[1]['data'],key=lambda x:x['id']))
existing=old[1]['data'][0]
request_body={key:existing[key] for key in ('orderId','userId','price')}
check('duplicate payment response matches deployed service',
      request(legacy,path,'POST',request_body,test_token())==
      request(candidate,path,'POST',request_body,test_token()))
responses={}
for label,base in (('legacy',legacy),('module',candidate)):
    body={'orderId':'MIGPAY-'+uuid.uuid4().hex,'userId':'migration-test-'+uuid.uuid4().hex,
          'price':'0.01'}
    status,response=request(base,path,'POST',body,test_token())
    check(label+' synthetic payment accepted',status==200 and response=={'status':1,'msg':'Pay Success','data':None})
    duplicate=request(base,path,'POST',body,test_token())
    check(label+' duplicate rejected',duplicate==(200,{'status':0,
          'msg':'Pay Failed, order not found with order id'+body['orderId'],'data':None}))
    status,listing=request(base,path,token=test_token())
    check(label+' payment retained',status==200 and any(row['orderId']==body['orderId'] and
          row['userId']==body['userId'] and row['price']==body['price'] for row in listing['data']))
    wallet={'userId':'migration-test-'+uuid.uuid4().hex,'price':'0.01'}
    responses[label]=request(base,path+'/money','POST',wallet,test_token())
    check(label+' addMoney response',responses[label]==(200,{'status':1,'msg':'Add Money Success',
          'data':{'userId':wallet['userId'],'money':wallet['price']}}))
check('addMoney response shape matches deployed service',
      (responses['legacy'][0],responses['legacy'][1]['status'],responses['legacy'][1]['msg'],
       set(responses['legacy'][1]['data']))==
      (responses['module'][0],responses['module'][1]['status'],responses['module'][1]['msg'],
       set(responses['module'][1]['data'])))
output=root/'ts-modulith/target/evidence/payment-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Payment candidate comparison passed')
