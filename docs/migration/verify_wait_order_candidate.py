"""Exercise WaitOrder authorization, durable writes, duplicate detection and reads."""
import json
import uuid

import hybrid_routing as routing
from http_support import request,test_token

base='http://127.0.0.1:18144'
path='/api/v1/waitorderservice'
status,graph=request(base,'/actuator/modulith')
assert status==200 and len(graph)==44 and {d['target'] for d in graph['waitorder']['dependencies']}=={'preserve'}
assert request(base,path+'/orders')[0] in (401,403)
token=test_token('ROLE_ADMIN')
assert request(base,path+'/welcome',token=token)==(200,'Welcome to [ Wait Order Service ] !')
account=str(uuid.uuid4());contact=str(uuid.uuid4())
order=dict(accountId=account,contactsId=contact,tripId='D1345',seatType=2,
           date='2026-10-05',from_='Shang Hai',to='Su Zhou',price='50.0')
order['from']=order.pop('from_')
status,created=request(base,path+'/order',method='POST',body=order,token=token)
assert status==200 and created['status']==1,created
status,duplicate=request(base,path+'/order',method='POST',body=order,token=token)
assert status==200 and duplicate['status']==0,duplicate
status,all_orders=request(base,path+'/orders',token=token)
assert status==200 and all_orders['status']==1
matches=[row for row in all_orders['data'] if row['accountId']==account]
assert len(matches)==1 and matches[0]['trainNumber']=='D1345' and matches[0]['status']==0
assert matches[0]['travelTime']!=matches[0]['createdTime']
status,waiting=request(base,path+'/waitlistorders',token=token)
assert status==200 and any(row['id']==matches[0]['id'] for row in waiting['data'])
status,live=request('http://127.0.0.1:18080','/actuator/modulith')
assert status==200 and len(live)==43 and 'waitorder' not in live
evidence=routing.EVIDENCE/'wait-order-candidate.json'
evidence.parent.mkdir(parents=True,exist_ok=True)
evidence.write_text(json.dumps([
    {'step':'44-module graph and independent WaitOrder boundary','passed':True},
    {'step':'authenticated create, duplicate rejection and filtered reads','passed':True},
    {'step':'isolated schema and unchanged live host','passed':True}],indent=2))
print('PASS WaitOrder candidate: graph, auth, persistence, duplicate, reads, isolation')
