"""Compare deployed/module OrderOther using isolated databases only."""
import copy
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

OUT = Path(__file__).resolve().parents[2] / 'ts-modulith/target/evidence'
BASES = ['http://127.0.0.1:22032', 'http://127.0.0.1:18084']
PREFIX = '/api/v1/orderOtherService'
TOKEN = test_token()
RESULTS = []
IDS = [None, None]
for base in BASES: wait_ready(base, PREFIX + '/orderOther')

def normalize(value, i):
    if isinstance(value,str) and value==IDS[i] and value is not None:return '<generated-order>'
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

all_orders=compare('all existing records including UUID and date encoding','/orderOther')[0][1]['data']
for order in all_orders[:3]:
    compare('read '+order['id'],'/orderOther/'+order['id'])
    compare('price '+order['id'],'/orderOther/price/'+order['id'])
query={'loginId':all_orders[0]['accountId'],'enableStateQuery':False,'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
compare('account query','/orderOther/query','POST',query)
compare('refresh uses Station names','/orderOther/refresh','POST',query)
query['enableStateQuery']=True;query['state']=0
compare('state-filtered query','/orderOther/query','POST',query)
query.update(enableStateQuery=False,enableBoughtDateQuery=True,boughtDateStart=0,boughtDateEnd=2000000000000)
compare('bought-date query','/orderOther/query','POST',query)
query.update(enableBoughtDateQuery=False,enableTravelDateQuery=True,travelDateStart=0,travelDateEnd=2000000000000)
compare('legacy travel-date-filter behaviour','/orderOther/query','POST',query)
missing=str(uuid.uuid4())
for suffix in [missing,'price/'+missing,'orderPay/'+missing,'status/'+missing+'/1']:
    compare('missing '+suffix,'/orderOther/'+suffix)
compare('missing delete','/orderOther/'+missing,'DELETE')
compare('sold tickets empty','/orderOther/tickets','POST',{'travelDate':2000000000000,'trainNumber':'MIGRATION-EMPTY'})
def authorization_difference(label,path,token):
    legacy=request(BASES[0],PREFIX+path,'POST',{},token)
    module=request(BASES[1],PREFIX+path,'POST',{},token)
    passed=legacy[0]==200 and legacy[1]['status']==1 and module[0]==403
    RESULTS.append(dict(label=label,passed=passed,legacy=legacy,module=module,intentional_security_correction=True))
    print('PASS' if passed else 'FAIL',label,flush=True)
    if legacy[0]==200 and legacy[1].get('status')==1:
        identifier=legacy[1]['data']['id']
        request(BASES[0],PREFIX+'/orderOther/'+identifier,'DELETE',token=TOKEN)

authorization_difference('anonymous create is rejected by module','/orderOther',None)
authorization_difference('USER cannot use admin create in module','/orderOther/admin',test_token('ROLE_USER'))
fixture={'accountId':str(uuid.uuid4()),'boughtDate':1800000000000,'travelDate':1800057600000,'travelTime':1800082800000,
         'contactsName':'Migration Test','documentType':1,'contactsDocumentNumber':'MIGRATION-ONLY','trainNumber':'MIGRATION-TEST',
         'coachNumber':1,'seatClass':2,'seatNumber':'5','from':'shanghai','to':'taiyuan','status':0,'price':'100.0'}
try:
    result=compare('create generates valid UUID','/orderOther','POST',fixture,created=True)
    assert all(IDS),result
    for identifier in IDS: uuid.UUID(identifier)
    compare('read created','/orderOther/{id}')
    compare('duplicate rejection','/orderOther','POST',fixture)
    compare('pay order GET mutates status','/orderOther/orderPay/{id}')
    compare('change order status GET','/orderOther/status/{id}/2')
    query={'loginId':fixture['accountId'],'enableStateQuery':False,'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
    compare('new order refresh uses local Station','/orderOther/refresh','POST',query)
    compare('sold tickets','/orderOther/tickets','POST',{'travelDate':fixture['travelDate'],'trainNumber':fixture['trainNumber']})
    updates=tuple(dict(fixture,id=identifier,price='110.0') for identifier in IDS)
    compare('update','/orderOther','PUT',updates)
    compare('admin update','/orderOther/admin','PUT',updates)
    compare('updated price','/orderOther/price/{id}')
    compare('delete','/orderOther/{id}','DELETE')
    compare('deleted record','/orderOther/{id}')
    compare('admin creates order','/orderOther/admin','POST',fixture,created=True)
finally:
    for base,identifier in zip(BASES,IDS):
        if identifier: request(base,PREFIX+'/orderOther/'+identifier,'DELETE',token=TOKEN)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'order-other-contracts.json').write_text(json.dumps(RESULTS,indent=2),encoding='utf-8')
failed=sum(not r['passed'] for r in RESULTS)
print(f'{len(RESULTS)-failed}/{len(RESULTS)} checks passed')
raise SystemExit(bool(failed))
