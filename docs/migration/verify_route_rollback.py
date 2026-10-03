"""Exercise Route rollback with a disposable record and return to module mode."""
import json
import uuid
from http_support import request
import hybrid_routing as routing

base='http://127.0.0.1:11178'
module='http://127.0.0.1:18080'
path='/api/v1/routeservice/routes'
route_id='migration-route-rollback-'+uuid.uuid4().hex
original={'id':route_id,'startStation':'a','endStation':'b',
          'stationList':'a,b','distanceList':'0,10'}
changed={**original,'distanceList':'0,20'}

def call(host,suffix='',method='GET',body=None):
    return request(host,path+suffix,method,body)

try:
    status,body=call(base,method='POST',body=original)
    assert status==200 and body['status']==1
    assert call(base,'/'+route_id)[1]['data']['distances']==[0,10]
    routing.switch('route','legacy')
    assert call(base,'/'+route_id)[1]['data']['distances']==[0,10]
    assert call(module,method='POST',body=changed)[0]==503
    status,body=call(base,method='POST',body=changed)
    assert status==200 and body['status']==1
    assert call(base,'/'+route_id)[1]['data']['distances']==[0,20]
    routing.switch('route','module')
    assert call(base,'/'+route_id)[1]['data']['distances']==[0,20]
    assert call(base,'/'+route_id,'DELETE')[1]['status']==1
    print('Route rollback passed: module create, legacy read/modify, module write gate, return and cleanup')
finally:
    state=json.loads(routing.DEFS['route']['file'].read_text())
    if state['mode']=='legacy':routing.switch('route','module')
    if call(base,'/'+route_id)[1].get('status')==1:
        call(base,'/'+route_id,'DELETE')
