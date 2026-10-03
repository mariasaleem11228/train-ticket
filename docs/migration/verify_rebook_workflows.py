"""Check Rebook refund, supplement and cross-family paths through port 8080."""
import datetime
import json
import uuid
import urllib.request
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=8)).date().isoformat()
orders='/api/v1/orderservice/order'
other='/api/v1/orderOtherService/orderOther'
token=test_token()
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def web(path,info):
    req=urllib.request.Request('http://127.0.0.1:8080/api/v1/rebookservice'+path,
                               data=json.dumps(info).encode(),method='POST',
                               headers={'Authorization':'Bearer '+token,
                                        'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:
        check(path+' uses Rebook module',response.status==200 and
              response.headers.get('X-Rebook-Backend')=='module')
        return json.loads(response.read())
status,source=request('http://127.0.0.1:12031',
                      orders+'/'+fixture['testOrders'][-1]['id'],token=token)
check('source order available',status==200 and source['status']==1)
def created(price):
    marker='migration-'+uuid.uuid4().hex
    order=dict(source['data']);order.pop('id',None)
    order.update(accountId=fixture['userId'],trainNumber='G1234',status=1,
                 price=price,travelDate=date,contactsDocumentNumber=marker)
    status,result=request('http://127.0.0.1:12031',orders,'POST',order,token)
    check('synthetic order created',status==200 and result['status']==1)
    return result['data']['id'],marker
def info(ident,new):
    return {'orderId':ident,'oldTripId':'G1234','tripId':new,'seatType':2,
            'date':date,'loginId':'migration-rebook-'+uuid.uuid4().hex}
def old(ident):
    return request('http://127.0.0.1:12031',orders+'/'+ident,token=token)[1]

ident,_=created('350.0');body=info(ident,'G1235')
result=web('/rebook',body)
check('cheaper trip rebooked',result['status']==1 and result['msg']=='Success!' and
      old(ident)['data']['status']==3 and old(ident)['data']['price']=='250.0')
status,balances=request('http://127.0.0.1:18673',
                        '/api/v1/inside_pay_service/inside_payment/account',token=token)
check('difference refunded to requested user',status==200 and any(
      row['userId']==body['loginId'] and row['balance']=='100.0'
      for row in balances['data']))

ident,_=created('50.0');body=info(ident,'G1235')
quote=web('/rebook',body)
check('higher fare quoted without changing order',quote['status']==2 and
      quote['data']['differenceMoney']=='200.0' and old(ident)['data']['status']==1)
result=web('/rebook/difference',body)
check('fare difference paid and order changed',result['status']==1 and
      old(ident)['data']['status']==3 and old(ident)['data']['price']=='250.0')
status,payments=request('http://127.0.0.1:18673',
                        '/api/v1/inside_pay_service/inside_payment/payment',token=token)
check('fare difference recorded for requested user',status==200 and any(
      row['userId']==body['loginId'] and row['orderId']==ident and
      row['price']=='200.0' and row['type']=='E' for row in payments['data']))

ident,marker=created('350.0');body=info(ident,'Z1236')
result=web('/rebook',body)
check('cross-family rebook accepted',result['status']==1 and result['msg']=='Success')
check('original order removed',old(ident)['status']==0)
status,target=request('http://127.0.0.1:12032',other,token=token)
matches=[row for row in target['data'] if row.get('contactsDocumentNumber')==marker]
check('replacement OrderOther retained',status==200 and len(matches)==1 and
      matches[0]['status']==3 and matches[0]['trainNumber']=='Z1236')

output=root/'ts-modulith/target/evidence/rebook-workflows.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Rebook browser-facing workflows passed')
