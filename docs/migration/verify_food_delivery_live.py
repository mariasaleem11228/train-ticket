"""Exercise the live Food Delivery module and its independent write gate."""
import json
import urllib.error
import urllib.request
import uuid

import hybrid_routing as routing

base='http://127.0.0.1:18080/api/v1/fooddeliveryservice'
order_id=str(uuid.uuid4())
body={'id':order_id,'stationFoodStoreId':'7b3e4704-9fcc-4c21-87a5-2b810b0b82c5',
      'foodList':[{'foodName':'Hamburger','price':999}],
      'tripId':'D1345','seatNo':3,'createdTime':'2026-10-03 10:00',
      'deliveryTime':'2026-10-03 11:00','deliveryFee':999}


def call(method,path,payload=None):
    request=urllib.request.Request(base+path,
        data=None if payload is None else json.dumps(payload).encode(),method=method,
        headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            raw=response.read().decode()
            return response.status,json.loads(raw) if raw.startswith('{') else raw
    except urllib.error.HTTPError as error:
        return error.code,error.read().decode()


with urllib.request.urlopen('http://127.0.0.1:18080/actuator/modulith',timeout=15) as response:
    graph=json.load(response)
assert len(graph)>=42 and graph['fooddelivery']['allowedDependencies']==['foodmap']
assert call('GET','/welcome')[1]=='Welcome to [ food delivery service ] !'
routing.owner('fooddelivery','maintenance')
try:
    assert call('POST','/orders',body)[0]==503
finally:
    routing.owner('fooddelivery','module')
try:
    status,created=call('POST','/orders',body)
    assert status==200 and created['status']==1 and created['data']['deliveryFee']==25.0,created
    assert call('GET','/orders/'+order_id)[1]['data']['id']==order_id
    assert call('PUT','/orders/seatno',{'orderId':order_id,'seatNo':8})[1]['data']['seatNo']==8
finally:
    call('DELETE','/orders/d/'+order_id)
assert call('GET','/orders/'+order_id)[1]['status']==0
print('PASS Food Delivery live graph, catalogue pricing, CRUD, and write gate')
