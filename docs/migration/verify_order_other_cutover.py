"""Rehearse OrderOther write continuity across module -> legacy -> module."""
import argparse
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
state=root/'deployment/migration/.state/e2e/order-other-cutover.json'
evidence=root/'ts-modulith/target/evidence/order-other-cutover.json'
prefix='/api/v1/orderOtherService/orderOther'
base='http://localhost:12032'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('action',choices=['create','rollback','cleanup'])
args=parser.parse_args()
token=test_token()

def call(label,path,method='GET',body=None):
    status,data=request(base,prefix+path,method,body,token)
    assert status==200 and data['status']==1,(label,status,data)
    print('PASS',label,flush=True)
    return data['data']

def save(item):
    state.parent.mkdir(parents=True,exist_ok=True)
    evidence.parent.mkdir(parents=True,exist_ok=True)
    state.write_text(json.dumps(item,indent=2))
    evidence.write_text(json.dumps({k:v for k,v in item.items() if k!='fixture'},indent=2))

if args.action=='create':
    assert not state.exists(),'Finish or inspect the previous rehearsal first'
    fixture={'accountId':str(uuid.uuid4()),'boughtDate':1800000000000,'travelDate':1800057600000,
        'travelTime':1800082800000,'contactsName':'Migration OrderOther','documentType':1,
        'contactsDocumentNumber':'MIGRATION-ORDEROTHER-ONLY','trainNumber':'MIGRATION-OTHER',
        'coachNumber':1,'seatClass':2,'seatNumber':'5','from':'shanghai','to':'taiyuan',
        'status':0,'price':'100.0'}
    created=call('module creates order','', 'POST',fixture)
    assert call('module reads new order','/'+created['id'])==created
    save({'id':created['id'],'accountId':fixture['accountId'],'phase':'created','fixture':fixture})
elif args.action=='rollback':
    item=json.loads(state.read_text());assert item['phase']=='created'
    order=call('legacy reads module-created order','/'+item['id'])
    assert order['accountId']==item['accountId']
    order['price']='110.0'
    call('legacy updates module-created order','', 'PUT',order)
    assert call('legacy reads updated order','/'+item['id'])['price']=='110.0'
    item['phase']='legacy-updated';save(item)
else:
    item=json.loads(state.read_text());assert item['phase']=='legacy-updated'
    order=call('module reads legacy-updated order','/'+item['id'])
    assert order['price']=='110.0'
    call('module deletes rehearsal order','/'+item['id'],'DELETE')
    status,data=request(base,prefix+'/'+item['id'],token=token)
    assert status==200 and data['status']==0
    item['phase']='complete';save(item)
print('OrderOther cutover phase:',args.action)
