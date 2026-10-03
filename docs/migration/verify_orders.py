"""Compare legacy/module Orders in isolated databases; never mutates live Orders."""
import copy
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

OUT = Path(__file__).resolve().parents[2] / 'ts-modulith/target/evidence'
BASES = ['http://127.0.0.1:22031', 'http://127.0.0.1:18082']
PREFIX = '/api/v1/orderservice'
TOKEN = test_token()
RESULTS = []
IDS = [None, None]
for base in BASES: wait_ready(base, PREFIX + '/order')

def normalize(value, i):
    if isinstance(value, dict):
        return {k: ('<generated-order>' if k=='id' and v==IDS[i] and v is not None else normalize(v,i)) for k,v in value.items()}
    if isinstance(value,list):
        converted=[normalize(v,i) for v in value]
        if converted and isinstance(converted[0],dict) and 'id' in converted[0]: converted.sort(key=lambda v:v['id'])
        return converted
    return value

def compare(label,path,method='GET',bodies=None,token=TOKEN,status_only=False,created=False):
    responses=[]
    for i,base in enumerate(BASES):
        body=bodies[i] if isinstance(bodies,tuple) else bodies
        response=request(base,PREFIX+path.replace('{id}',IDS[i] or 'missing'),method,body,token)
        if created and response[0]==200 and response[1].get('status')==1: IDS[i]=response[1]['data']['id']
        responses.append(response)
    passed = responses[0][0]==responses[1][0] if status_only else (responses[0][0]==responses[1][0] and normalize(responses[0][1],0)==normalize(responses[1][1],1))
    RESULTS.append(dict(label=label,passed=passed,legacy=responses[0],module=responses[1]))
    print('PASS' if passed else 'FAIL',label,flush=True)
    return responses

all_orders=compare('all existing records including UUID and date encoding','/order')[0][1]['data']
for order in all_orders[:3]:
    compare('read '+order['id'],'/order/'+order['id'])
    compare('price '+order['id'],'/order/price/'+order['id'])
query={'loginId':all_orders[0]['accountId'],'enableStateQuery':False,'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
compare('account query','/order/query','POST',query)
compare('refresh uses Station names','/order/refresh','POST',query)
query['enableStateQuery']=True;query['state']=0
compare('state-filtered query','/order/query','POST',query)
query.update(enableStateQuery=False,enableBoughtDateQuery=True,boughtDateStart=0,boughtDateEnd=2000000000000)
compare('bought-date query','/order/query','POST',query)
query.update(enableBoughtDateQuery=False,enableTravelDateQuery=True,travelDateStart=0,travelDateEnd=2000000000000)
compare('legacy travel-date-filter behaviour','/order/query','POST',query)
missing=str(uuid.uuid4())
for suffix in [missing,'price/'+missing,'orderPay/'+missing,'status/'+missing+'/1']:
    compare('missing '+suffix,'/order/'+suffix)
compare('missing delete','/order/'+missing,'DELETE')
compare('sold tickets empty','/order/tickets','POST',{'travelDate':2000000000000,'trainNumber':'MIGRATION-EMPTY'})
compare('anonymous create','/order','POST',{},token=None,status_only=True)
compare('user cannot administer','/order/admin','POST',{},token=test_token('ROLE_USER'),status_only=True)
fixture={'accountId':str(uuid.uuid4()),'boughtDate':1800000000000,'travelDate':1800057600000,'travelTime':1800082800000,
         'contactsName':'Migration Test','documentType':1,'contactsDocumentNumber':'MIGRATION-ONLY','trainNumber':'MIGRATION-TEST',
         'coachNumber':1,'seatClass':2,'seatNumber':'5','from':'shanghai','to':'taiyuan','status':0,'price':'100.0'}
try:
    result=compare('create generates valid UUID','/order','POST',fixture,created=True)
    assert all(IDS),result
    for identifier in IDS: uuid.UUID(identifier)
    compare('read created','/order/{id}')
    compare('duplicate rejection','/order','POST',fixture)
    compare('pay order GET mutates status','/order/orderPay/{id}')
    compare('change order status GET','/order/status/{id}/2')
    query={'loginId':fixture['accountId'],'enableStateQuery':False,'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
    compare('new order refresh uses local Station','/order/refresh','POST',query)
    compare('sold tickets','/order/tickets','POST',{'travelDate':fixture['travelDate'],'trainNumber':fixture['trainNumber']})
    updates=tuple(dict(fixture,id=identifier,price='110.0') for identifier in IDS)
    compare('update','/order','PUT',updates)
    compare('admin update','/order/admin','PUT',updates)
    compare('updated price','/order/price/{id}')
    compare('delete','/order/{id}','DELETE')
    compare('deleted record','/order/{id}')
    compare('admin creates order','/order/admin','POST',fixture,created=True)
finally:
    for base,identifier in zip(BASES,IDS):
        if identifier: request(base,PREFIX+'/order/'+identifier,'DELETE',token=TOKEN)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'orders-contracts.json').write_text(json.dumps(RESULTS,indent=2),encoding='utf-8')
failed=sum(not r['passed'] for r in RESULTS)
print(f'{len(RESULTS)-failed}/{len(RESULTS)} checks passed')
raise SystemExit(bool(failed))
