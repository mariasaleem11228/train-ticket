"""Exercise durable retry, order idempotency, ownership and expiry in isolation."""
import datetime
import json
import random
import subprocess
import time
import uuid

import hybrid_routing as routing
from http_support import request,test_token

base='http://127.0.0.1:18145'
path='/api/v1/waitorderservice'
fixture=json.loads((routing.STATE/'e2e/fixture.json').read_text())
account,contact=fixture['userId'],fixture['contactId']
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=random.randint(7,21))).strftime('%Y-%m-%d')
admin=test_token('ROLE_ADMIN')
user=test_token('ROLE_USER',account)
wrong=test_token('ROLE_USER',str(uuid.uuid4()))
search={'startingPlace':'Nan Jing','endPlace':'Shang Hai','departureTime':date}
status,trips=request(base,'/api/v1/travelservice/trips/left','POST',search,admin)
assert status==200 and trips['status']==1 and trips['data'],trips
trip=trips['data'][0]['tripId']
if isinstance(trip,dict):trip=str(trip['type'])+str(trip['number'])
body={'accountId':account,'contactsId':contact,'tripId':trip,'seatType':3,
      'date':date,'from':'Nan Jing','to':'Shang Hai','price':'50.0'}
assert request(base,path+'/order','POST',body,wrong)[0]==403
status,created=request(base,path+'/order','POST',body,user)
assert status==200 and created['status']==1,created
assert request(base,path+'/order','POST',body,user)[1]['status']==0

def sql(query):
    return routing.docker('exec','station-migration-wait-order-mysql-1',
                          'mysql','-N','-B','-uroot','-proot','wait_order_retry_candidate',
                          '-e',query).rstrip('\r\n')

deadline=time.monotonic()+50
while time.monotonic()<deadline:
    raw=sql("SELECT id,status,COALESCE(booking_order_id,''),attempt_count "
            "FROM wait_list_order WHERE account_id='"+account+"' ORDER BY created_time DESC LIMIT 1")
    if raw:
        wait_id,state,order_id,attempts=raw.split('\t')
        if state=='2' and order_id:break
    time.sleep(2)
else:raise AssertionError('WaitOrder did not book in isolated candidate: '+str(raw))
status,order=request(base,'/api/v1/orderservice/order/'+order_id,token=admin)
assert status==200 and order['status']==1 and order['data']['accountId']==account,order
sql("UPDATE wait_list_order SET status=0,next_attempt=NULL,lease_token=NULL,lease_until=NULL "
    "WHERE id='"+wait_id+"'")
deadline=time.monotonic()+30
while time.monotonic()<deadline:
    raw=sql("SELECT status,booking_order_id,attempt_count FROM wait_list_order WHERE id='"+wait_id+"'")
    state,replayed_id,replayed_attempts=raw.split('\t')
    if state=='2' and int(replayed_attempts)>int(attempts):break
    time.sleep(2)
else:raise AssertionError('WaitOrder replay did not finish')
assert replayed_id==order_id
status,orders=request(base,'/api/v1/orderservice/order',token=admin)
assert status==200 and sum(item['id']==order_id for item in orders['data'])==1,orders
bad_contact=str(uuid.uuid4())
failed=dict(body,contactsId=bad_contact)
assert request(base,path+'/order','POST',failed,user)[1]['status']==1
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    raw=sql("SELECT id,status,attempt_count FROM wait_list_order "
            "WHERE contacts_id='"+bad_contact+"' LIMIT 1")
    if raw:
        failed_id,failed_state,failed_attempts=raw.split('\t')
        if int(failed_attempts)>0:break
    time.sleep(2)
else:raise AssertionError('Failed booking was not retried')
failed_error=sql("SELECT COALESCE(last_error,'') FROM wait_list_order WHERE id='"+failed_id+"'")
assert failed_state=='0' and failed_error
sql("UPDATE wait_list_order SET wait_util_time=DATE_SUB(CURRENT_TIMESTAMP(3), INTERVAL 1 SECOND) "
    "WHERE id='"+failed_id+"'")
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    if sql("SELECT status FROM wait_list_order WHERE id='"+failed_id+"'")=='5':break
    time.sleep(2)
else:raise AssertionError('Expired wait order remained active')
evidence=routing.EVIDENCE/'wait-order-retry-candidate.json'
evidence.write_text(json.dumps([
    {'step':'user may only create own wait-list entry','passed':True},
    {'step':'wait-list entry books into isolated Orders database','passed':True},
    {'step':'replayed retry keeps the same order ID','passed':True},
    {'step':'failed booking backs off and expired entry is closed','passed':True}],indent=2))
print('PASS WaitOrder retry: owner check, booking, replay, failure, expiry')
