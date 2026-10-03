"""Exercise Price rollback with a disposable record and return to module mode."""
import json
import uuid
from http_support import request
import hybrid_routing as routing

base='http://127.0.0.1:16579'
module='http://127.0.0.1:18080'
path='/api/v1/priceservice/prices'
original={'id':str(uuid.uuid4()),'routeId':'migration-price-rollback-'+uuid.uuid4().hex,
          'trainType':'migration-train','basicPriceRate':0.3,'firstClassPriceRate':0.8}
changed={**original,'basicPriceRate':0.4}
lookup='/'+original['routeId']+'/'+original['trainType']

def call(host,suffix='',method='GET',body=None):
    return request(host,path+suffix,method,body)

try:
    status,body=call(base,method='POST',body=original)
    assert status==201 and body['status']==1
    assert call(base,lookup)[1]['data']['basicPriceRate']==0.3
    routing.switch('price','legacy')
    assert call(base,lookup)[1]['data']['basicPriceRate']==0.3
    assert call(module,method='PUT',body=changed)[0]==503
    status,body=call(base,method='PUT',body=changed)
    assert status==200 and body['status']==1
    assert call(base,lookup)[1]['data']['basicPriceRate']==0.4
    routing.switch('price','module')
    assert call(base,lookup)[1]['data']['basicPriceRate']==0.4
    assert call(base,method='DELETE',body=changed)[1]['status']==1
    print('Price rollback passed: module create, legacy read/update, module write gate, return and cleanup')
finally:
    state=json.loads(routing.DEFS['price']['file'].read_text())
    if state['mode']=='legacy':routing.switch('price','module')
    if call(base,lookup)[1].get('status')==1:
        call(base,method='DELETE',body=changed)
