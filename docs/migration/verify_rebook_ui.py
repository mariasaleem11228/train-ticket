"""Exercise browser-facing Rebook API through port 8080 with a synthetic order."""
import datetime
import json
import uuid
import urllib.request
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=8)).date().isoformat()
order_path='/api/v1/orderservice/order'
status,source=request('http://127.0.0.1:12031',
                      order_path+'/'+fixture['testOrders'][-1]['id'],token=test_token())
assert status==200 and source['status']==1,'Source order unavailable'
order=dict(source['data']);order.pop('id',None)
order.update(accountId=fixture['userId'],trainNumber='G1234',status=1,
             price='250.0',travelDate=date,
             contactsDocumentNumber='migration-'+uuid.uuid4().hex)
status,created=request('http://127.0.0.1:12031',order_path,'POST',order,test_token())
assert status==200 and created['status']==1,'Synthetic order creation failed'
ident=created['data']['id']
info={'orderId':ident,'oldTripId':'G1234','tripId':'G1235','seatType':2,
      'date':date,'loginId':'migration-rebook-'+uuid.uuid4().hex}
web=urllib.request.Request('http://127.0.0.1:8080/api/v1/rebookservice/rebook',
                           data=json.dumps(info).encode(),method='POST',
                           headers={'Authorization':'Bearer '+test_token(),
                                    'Content-Type':'application/json'})
with urllib.request.urlopen(web,timeout=30) as response:
    backend=response.headers.get('X-Rebook-Backend')
    result=json.loads(response.read())
    assert response.status==200 and backend=='module' and result['status']==1 and \
           result['msg']=='Success!','UI Rebook response'
print('PASS browser-facing rebook route uses Rebook module')
status,updated=request('http://127.0.0.1:12031',order_path+'/'+ident,token=test_token())
assert status==200 and updated['status']==1 and updated['data']['status']==3 and \
       updated['data']['trainNumber']=='G1235','Rebooked order not retained'
print('PASS browser-facing rebook updated synthetic order')
output=root/'ts-modulith/target/evidence/rebook-ui.json'
output.write_text(json.dumps({'orderId':ident,'backend':backend,'passed':True},indent=2),
                  encoding='utf-8')
print('Rebook UI route passed')
