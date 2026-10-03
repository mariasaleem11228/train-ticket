"""Exercise all Food Delivery endpoints against the isolated candidate."""
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:18142/api/v1/fooddeliveryservice'


def call(method,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(base+path,data=data,method=method,
                                   headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=15) as response:
        raw=response.read().decode()
        return json.loads(raw) if raw.startswith('{') else raw


with urllib.request.urlopen('http://127.0.0.1:18142/actuator/modulith',timeout=15) as response:
    graph=json.load(response)
assert len(graph)==42 and graph['fooddelivery']['allowedDependencies']==['foodmap']
assert call('GET','/welcome')=='Welcome to [ food delivery service ] !'
store_id='7b3e4704-9fcc-4c21-87a5-2b810b0b82c5'
order_id=str(uuid.uuid4())
body={'id':order_id,'stationFoodStoreId':store_id,
      'foodList':[{'foodName':'Hamburger','price':999}],
      'tripId':'D1345','seatNo':3,'createdTime':'2026-10-03 10:00',
      'deliveryTime':'2026-10-03 11:00','deliveryFee':999}
invalid={**body,'id':str(uuid.uuid4()),'foodList':[{'foodName':'Missing Food','price':1}]}
assert call('POST','/orders',invalid)['msg']=='Food not in store'
created=call('POST','/orders',body)
assert created['status']==1 and created['data']['deliveryFee']==25.0,created
assert call('GET','/orders/'+order_id)['data']['id']==order_id
assert any(row['id']==order_id for row in call('GET','/orders/all')['data'])
assert any(row['id']==order_id for row in call('GET','/orders/store/'+store_id)['data'])
assert call('PUT','/orders/tripid',{'orderId':order_id,'tripId':'G1234'})['data']['tripId']=='G1234'
assert call('PUT','/orders/seatno',{'orderId':order_id,'seatNo':8})['data']['seatNo']==8
assert call('PUT','/orders/dtime',{'orderId':order_id,'deliveryTime':'later'})['data']['deliveryTime']=='later'
assert call('DELETE','/orders/d/'+order_id)['status']==1
assert call('GET','/orders/'+order_id)['status']==0
assert call('DELETE','/orders/d/'+order_id)['status']==0
with urllib.request.urlopen('http://127.0.0.1:18080/actuator/modulith',timeout=15) as response:
    live=json.load(response)
assert len(live)==41 and 'fooddelivery' not in live
evidence=root/'ts-modulith/target/evidence/food-delivery-candidate.json'
evidence.parent.mkdir(parents=True,exist_ok=True)
evidence.write_text(json.dumps([
    {'step':'Food Delivery is module 42 using Food Map','passed':True},
    {'step':'isolated candidate validates catalogue pricing and CRUD','passed':True},
    {'step':'live 41-module host unchanged','passed':True}],indent=2))
print('PASS Food Delivery candidate: graph, pricing, CRUD, live host unchanged')
