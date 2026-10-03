"""Exercise the Order List payment API through browser-facing port 8080."""
import json
import uuid
import urllib.request
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
order_path='/api/v1/orderservice/order'
source=request('http://127.0.0.1:12031',order_path+'/'+fixture['testOrders'][-1]['id'],
               token=test_token())
if source[0]!=200 or source[1]['status']!=1:raise AssertionError('Source order unavailable')
user=str(uuid.uuid4())
order=dict(source[1]['data']);order.pop('id',None)
order.update(accountId=user,trainNumber='D1345',status=0,price='50.0')
status,created=request('http://127.0.0.1:12031',order_path,'POST',order,test_token())
if status!=200 or created['status']!=1:raise AssertionError('Synthetic order creation failed')
ident=created['data']['id']
# The current Order List JavaScript sends no userId.
body=json.dumps({'orderId':ident,'tripId':'D1345'}).encode()
web=urllib.request.Request('http://127.0.0.1:8080/api/v1/inside_pay_service/inside_payment',
                           data=body,headers={'Authorization':'Bearer '+test_token(),
                                              'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(web,timeout=30) as response:
    backend=response.headers.get('X-InsidePayment-Backend')
    result=json.loads(response.read())
    assert response.status==200 and backend=='module' and result=={
        'status':1,'msg':'Payment Success Pay Success','data':None},'UI payment response'
print('PASS browser-facing payment route uses Inside Payment module')
status,updated=request('http://127.0.0.1:12031',order_path+'/'+ident,token=test_token())
assert status==200 and updated['status']==1 and updated['data']['status']==1,'Order not paid'
print('PASS browser-facing payment updated synthetic order')
status,payments=request('http://127.0.0.1:19001','/api/v1/paymentservice/payment',token=test_token())
assert status==200 and any(row['orderId']==ident for row in payments['data']),'Outside Payment missing'
print('PASS outside Payment module retained payment')
output=root/'ts-modulith/target/evidence/inside-payment-ui.json'
output.write_text(json.dumps({'orderId':ident,'backend':backend,'passed':True},indent=2),encoding='utf-8')
print('Inside Payment UI route passed')
