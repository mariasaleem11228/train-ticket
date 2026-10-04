"""Book one standard and one other trip with isolated order databases."""
import datetime
import json
import random
import time

import hybrid_routing as routing
from http_support import request,test_token,wait_ready

name='trip-catalog-booking-candidate'
base='http://127.0.0.1:18149'
if name in routing.docker('ps','-a','--format','{{.Names}}').splitlines():
    raise RuntimeError(name+' already exists; inspect before replacing it')
host=json.loads(routing.docker('inspect','station-migration-modulith-1'))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
database='trip_catalog_booking_'+str(int(time.time()))
env.update(SEAT_TRAVEL_URL='http://127.0.0.1:1',
           SEAT_TRAVEL2_URL='http://127.0.0.1:1',
           ORDER_WRITES_ENABLED='true',ORDER_OTHER_WRITES_ENABLED='true',
           PRESERVE_WRITES_ENABLED='true',PRESERVE_OTHER_WRITES_ENABLED='true',
           ORDER_MONGO_URI='mongodb://ts-order-mongo:27017/'+database,
           ORDER_OTHER_MONGO_URI='mongodb://ts-order-other-mongo:27017/'+database,
           WAIT_ORDER_RETRY_ENABLED='false',MODULITH_OWNERSHIP_FILE='')
env_path=routing.ROOT/'ts-modulith/target/trip-catalog-booking-candidate.env'
env_path.write_text(''.join(f'{key}={value}\n' for key,value in env.items()),encoding='utf-8')
try:
    routing.docker('run','-d','--name',name,'--network','train-ticket_my-network',
                   '-p','127.0.0.1:18149:18080','--env-file',str(env_path),
                   'train-ticket/ts-modulith:trip-catalog-candidate')
    wait_ready(base,'/actuator/health',seconds=180)
    graph=request(base,'/actuator/modulith')[1]
    assert len(graph)==45 and 'tripcatalog' in graph
    fixture=json.loads((routing.STATE/'e2e/fixture.json').read_text())
    account,contact=fixture['userId'],fixture['contactId']
    date=(datetime.datetime.now(datetime.timezone.utc)+
          datetime.timedelta(days=random.randint(7,21))).strftime('%Y-%m-%d')
    token=test_token('ROLE_ADMIN')
    for service,booking,orders in (
        ('travelservice','/api/v1/preserveservice/preserve','/api/v1/orderservice/order'),
        ('travel2service','/api/v1/preserveotherservice/preserveOther',
         '/api/v1/orderOtherService/orderOther')):
        query={'startingPlace':'Nan Jing','endPlace':'Shang Hai','departureTime':date}
        status,trips=request(base,'/api/v1/'+service+'/trips/left','POST',query,token)
        assert status==200 and trips['status']==1 and trips['data'],(service,trips)
        trip=trips['data'][0]['tripId']
        number=trip if isinstance(trip,str) else str(trip['type'])+str(trip['number'])
        body={'accountId':account,'contactsId':contact,'tripId':number,
              'seatType':3,'date':date,'from':'Nan Jing','to':'Shang Hai',
              'assurance':0,'foodType':0}
        status,booked=request(base,booking,'POST',body,token)
        assert status==200 and booked['status']==1,(service,booked)
        status,listed=request(base,orders,token=token)
        assert status==200 and listed['status']==1 and len(listed['data'])==1,(service,listed)
        assert listed['data'][0]['trainNumber']==number,(service,listed)
    print('PASS Trip Catalog booking: Travel and Travel2 reserve through local Seat lookup')
    routing.EVIDENCE.mkdir(parents=True,exist_ok=True)
    (routing.EVIDENCE/'trip-catalog-booking-candidate.json').write_text(json.dumps([
        {'step':'standard booking persists in isolated Orders database','passed':True},
        {'step':'other booking persists in isolated OrderOther database','passed':True}],indent=2),encoding='utf-8')
finally:
    if name in routing.docker('ps','-a','--format','{{.Names}}').splitlines():
        routing.docker('stop',name)
        routing.docker('rm',name)
    env_path.unlink(missing_ok=True)
