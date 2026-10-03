"""Remove only the sample order created by our first legacy router startup."""
import json
import time
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
evidence=root/'ts-modulith/target/evidence'
baseline=json.loads((evidence/'order-other-contracts.json').read_text())[0]['legacy'][1]['data']
base_ids={row['id'] for row in baseline}
prefix='/api/v1/orderOtherService/orderOther'
status,response=request('http://localhost:12032',prefix,token=test_token())
assert status==200 and response['status']==1
extra=[row for row in response['data'] if row['id'] not in base_ids]
assert len(extra)==1,extra
sample=extra[0]
assert sample['contactsName']=='Test' and sample['contactsDocumentNumber']=='Test'
assert sample['trainNumber']=='K1235' and sample['seatNumber']=='6A'
assert sample['accountId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f'
assert 0 <= int(time.time()*1000)-sample['boughtDate'] < 3600000
result=request('http://localhost:12032',prefix+'/'+sample['id'],'DELETE',token=test_token())
assert result[0]==200 and result[1]['status']==1,result
status,response=request('http://localhost:12032',prefix,token=test_token())
assert status==200 and {row['id'] for row in response['data']}==base_ids
(evidence/'order-other-seed-reconciliation.json').write_text(json.dumps({'removed_synthetic_id':sample['id'],'original_ids_preserved':sorted(base_ids)},indent=2))
print('Removed one startup sample; original OrderOther records preserved')
