"""Exercise OrderOther through the local hybrid with a dedicated synthetic account and local mail sink.

Run with a stage name. Credentials/token are kept only in ignored runtime state.
Cancelled test orders and the test wallet remain for audit; no existing user is used.
"""
import argparse
import datetime
import json
import uuid
from decimal import Decimal
import urllib.request
from pathlib import Path
from http_support import request, test_token

ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'deployment/migration/.state/e2e'
STATE.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('stage')
parser.add_argument('--preserve-other-port', type=int, default=14569,
                    help='Port for PreserveOther booking requests; use 8080 to test the UI gateway')
args=parser.parse_args()
fixture_path=STATE/'fixture.json'
if not fixture_path.exists():
    raise SystemExit('Synthetic fixture is missing. Preserve the existing .state/e2e/fixture.json; see TESTING.md.')
(ROOT/'ts-modulith/target/evidence').mkdir(parents=True,exist_ok=True)
fixture=json.loads(fixture_path.read_text())
results=[]

def call(label,port,path,method='GET',body=None,token=None):
    credential=fixture['token'] if token is None else (None if token is False else token)
    status,data=request(f'http://127.0.0.1:{port}',path,method,body,credential)
    ok=status in (200,201) and isinstance(data,dict) and data.get('status')==1
    results.append({'step':label,'passed':ok,'http_status':status,'message':data.get('msg') if isinstance(data,dict) else str(data)[:100]})
    print(label,status,results[-1]['message'],flush=True)
    save()
    if not ok: raise RuntimeError(label+' failed: '+str(data)[:800])
    return data.get('data')

def save():
    (ROOT/f'ts-modulith/target/evidence/booking-other-{args.stage}.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    fixture_path.write_text(json.dumps(fixture),encoding='utf-8')

def check(label,condition):
    results.append({'step':label,'passed':bool(condition)})
    save()
    if not condition: raise AssertionError(label)

def balance(label):
    accounts=call(label,18673,'/api/v1/inside_pay_service/inside_payment/account')
    return Decimal(next(a['balance'] for a in accounts if a['userId']==fixture['userId']))

# Explicitly verify the email sink is running before any booking can send a message.
with urllib.request.urlopen('http://127.0.0.1:8025/api/v1/info',timeout=10) as r:
    assert r.status==200
login=call('login',12340,'/api/v1/users/login','POST',{'username':fixture['userName'],'password':fixture['password'],'verificationCode':''},token=False)
fixture['token']=login['token']
if 'contactId' not in fixture:
    contact=call('create test contact',12347,'/api/v1/contactservice/contacts','POST',
                 {'id':str(uuid.uuid4()),'accountId':fixture['userId'],'name':'Migration Test','documentType':1,
                  'documentNumber':'MIGRATION-'+fixture['userName'],'phoneNumber':'0000000000'})
    fixture['contactId']=contact['id'];save()
if not fixture.get('walletCreated'):
    call('create test wallet',18673,'/api/v1/inside_pay_service/inside_payment/account','POST',{'userId':fixture['userId'],'money':'10000'})
    fixture['walletCreated']=True;save()
date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=7)).strftime('%Y-%m-%d')
journeys=call('search through UI',8080,'/api/v1/travel2service/trips/left','POST',{'startingPlace':'Nan Jing','endPlace':'Shang Hai','departureTime':date})
check('search returns actual journeys',bool(journeys))
trip=journeys[0]['tripId']
if isinstance(trip,dict): trip=str(trip['type'])+str(trip['number'])
query={'loginId':fixture['userId'],'enableStateQuery':False,'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
previous=call('orders before booking',12031,'/api/v1/orderOtherService/orderOther/query','POST',query)
previous_ids={order['id'] for order in previous}
call('book through PreserveOther',args.preserve_other_port,'/api/v1/preserveotherservice/preserveOther','POST',
     {'accountId':fixture['userId'],'contactsId':fixture['contactId'],'tripId':trip,'seatType':2,'date':date,
      'from':'Nan Jing','to':'Shang Hai','assurance':0,'foodType':0,'consigneeName':'','consigneePhone':'','consigneeWeight':0})
orders=call('read booked order',12031,'/api/v1/orderOtherService/orderOther/query','POST',query)
created=[order for order in orders if order['id'] not in previous_ids]
assert len(created)==1,created
order=created[0]
fixture.setdefault('testOtherOrders',[]).append({'stage':args.stage,'id':order['id']});save()
before_balance=balance('wallet before payment')
call('pay from test wallet',18673,'/api/v1/inside_pay_service/inside_payment','POST',
     {'orderId':order['id'],'tripId':trip,'userId':fixture['userId'],'price':order['price']})
paid=call('verify paid order',12031,'/api/v1/orderOtherService/orderOther/'+order['id'])
check('paid status is 1',paid['status']==1)
check('wallet charged exact fare',balance('wallet after payment')==before_balance-Decimal(order['price']))
refund=call('refund quote',18885,'/api/v1/cancelservice/cancel/refound/'+order['id'])
call('cancel and refund',18885,'/api/v1/cancelservice/cancel/'+order['id']+'/'+fixture['userId'])
cancelled=call('verify cancelled order',12031,'/api/v1/orderOtherService/orderOther/'+order['id'])
check('cancelled status is 4',cancelled['status']==4)
check('wallet credited quoted refund',balance('wallet after cancellation')==before_balance-Decimal(order['price'])+Decimal(str(refund)))
fixture['testOtherOrders'][-1]['cancelled']=True;save()
print('Booking/payment/cancellation sequence passed; synthetic fixtures retained for audit')
