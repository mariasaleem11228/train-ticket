"""Compare local trip/seat reads with the live hybrid while HTTP lookup is disabled."""
import datetime
import json
from pathlib import Path

import hybrid_routing as routing
from http_support import request, test_token, wait_ready

name='trip-catalog-candidate'
candidate='http://127.0.0.1:18148'
live='http://127.0.0.1:18080'
if name in routing.docker('ps','-a','--format','{{.Names}}').splitlines():
    raise RuntimeError(name+' already exists; inspect before replacing it')
host=json.loads(routing.docker('inspect','station-migration-modulith-1'))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(SEAT_TRAVEL_URL='http://127.0.0.1:1',
           SEAT_TRAVEL2_URL='http://127.0.0.1:1',
           WAIT_ORDER_RETRY_ENABLED='false',MODULITH_OWNERSHIP_FILE='')
env_path=routing.ROOT/'ts-modulith/target/trip-catalog-candidate.env'
env_path.write_text(''.join(f'{key}={value}\n' for key,value in env.items()),encoding='utf-8')
checks=[]
try:
    routing.docker('run','-d','--name',name,'--network','train-ticket_my-network',
                   '-p','127.0.0.1:18148:18080','--env-file',str(env_path),
                   'train-ticket/ts-modulith:trip-catalog-candidate')
    wait_ready(candidate,'/actuator/health',seconds=180)
    status,graph=request(candidate,'/actuator/modulith')
    assert status==200 and len(graph)==45 and graph['tripcatalog']['dependencies']==[]
    assert {d['target'] for d in graph['seat']['dependencies']}=={
        'orders','orderother','config','tripcatalog','route','train'}
    checks.append('45-module graph has an acyclic Seat-to-Trip Catalog path')
    date=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    token=test_token()
    for service in ('travelservice','travel2service'):
        prefix='/api/v1/'+service
        query={'startingPlace':'Nan Jing','endPlace':'Shang Hai','departureTime':date}
        old=request(live,prefix+'/trips/left','POST',query,token)
        new=request(candidate,prefix+'/trips/left','POST',query,token)
        assert old==new and new[0]==200 and new[1]['data'],(service,old,new)
        checks.append(service+' search matches live')
        trip=new[1]['data'][0]['tripId']
        number=trip if isinstance(trip,str) else str(trip['type'])+str(trip['number'])
        for resource in ('routes','train_types'):
            old=request(live,prefix+'/'+resource+'/'+number,token=token)
            new=request(candidate,prefix+'/'+resource+'/'+number,token=token)
            assert old==new and new[0]==200,(service,resource,old,new)
            checks.append(service+' '+resource+' matches live')
        route=request(candidate,prefix+'/routes/'+number,token=token)[1]['data']
        assert route['stations'] and len(route['stations'])>=2,route
        for seat_type in (2,3):
            body={'travelDate':date,'trainNumber':number,
                  'startStation':route['stations'][0],
                  'destStation':route['stations'][-1],'seatType':seat_type}
            path='/api/v1/seatservice/seats/left_tickets'
            old=request(live,path,'POST',body,token)
            new=request(candidate,path,'POST',body,token)
            assert old==new and new[0]==200,(number,seat_type,old,new)
            checks.append(number+' class '+str(seat_type)+' seat availability matches live')
    print('PASS Trip Catalog candidate:',len(checks),'graph and live contract checks')
    routing.EVIDENCE.mkdir(parents=True,exist_ok=True)
    (routing.EVIDENCE/'trip-catalog-candidate.json').write_text(
        json.dumps([{'step':item,'passed':True} for item in checks],indent=2),encoding='utf-8')
finally:
    if name in routing.docker('ps','-a','--format','{{.Names}}').splitlines():
        routing.docker('stop',name)
        routing.docker('rm',name)
    env_path.unlink(missing_ok=True)
