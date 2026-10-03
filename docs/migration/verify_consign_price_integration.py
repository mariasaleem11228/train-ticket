"""Exercise a synthetic Consign booking through the UI gateway and routed price module."""
import json
import subprocess
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
order_id=str(uuid.uuid4())
account_id=str(uuid.uuid4())
marker='migration-consign-price-'+uuid.uuid4().hex
payload={'orderId':order_id,'accountId':account_id,'handleDate':'2026-10-02',
         'targetDate':'2026-10-03','from':'Shang Hai','to':'Nan Jing',
         'consignee':marker,'phone':'1234567890','weight':3.0,'isWithin':False}
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

status,quote=request('http://127.0.0.1:16110',
        '/api/v1/consignpriceservice/consignprice/3/false',token=test_token('ROLE_USER'))
check('routed module quotes consignment',status==200 and quote=={'status':1,'msg':'Success','data':16.0})
record_id=None
try:
    status,result=request('http://127.0.0.1:8080','/api/v1/consignservice/consigns',
                          'POST',payload,test_token('ROLE_USER'))
    if isinstance(result,dict) and isinstance(result.get('data'),dict):
        record_id=result['data'].get('id')
    check('Consign microservice created shipment using module price',
          status==200 and result['status']==1 and result['data']['price']==16.0
          and result['data']['consignee']==marker)
    status,lookup=request('http://127.0.0.1:16111',
                          '/api/v1/consignservice/consigns/order/'+order_id,
                          token=test_token('ROLE_USER'))
    check('synthetic shipment visible through Consign',status==200 and
          lookup['status']==1 and lookup['data']['id']==record_id)
finally:
    if record_id:
        names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
        matches=[name for name in names if name.endswith('train-ticket-ts-consign-mongo-1')]
        if len(matches)!=1:raise RuntimeError('Expected one Consign Mongo container')
        js='db.getSiblingDB("ts").consign_record.deleteOne({consignee:"'+marker+'"})'
        result=subprocess.check_output(['docker','exec',matches[0],'mongo','--quiet','--eval',js],text=True)
        check('synthetic shipment removed', '"deletedCount" : 1' in result)
output=root/'ts-modulith/target/evidence/consign-price-integration.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ConsignPrice integration passed')
