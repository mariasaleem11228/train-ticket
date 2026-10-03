"""Compare Food API behavior using isolated copies of its Mongo orders."""
import json
import subprocess
import uuid
from pathlib import Path
from http_support import request

root=Path(__file__).resolve().parents[2]
live='http://127.0.0.1:18856'
legacy='http://127.0.0.1:28856'
module='http://127.0.0.1:18118'
prefix='/api/v1/foodservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def call(base,path,method='GET',body=None):return request(base,prefix+path,method,body)

def queue_count(name):
    output=subprocess.check_output(['docker','exec','migration-infra-rabbitmq-1',
                                    'rabbitmqctl','list_queues','-q','name','messages_ready'],text=True)
    return int(dict(line.split('\t') for line in output.splitlines()[1:])[name])

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('27 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'food'})
check('Food uses local catalogue and journey modules',
      {edge['target'] for edge in graph['food']['dependencies']}=={'foodmap','travel','station','route'})
check('welcome matches',call(live,'/welcome')==call(module,'/welcome'))
check('existing orders match',call(live,'/orders')==call(module,'/orders'))
existing=call(live,'/orders')[1]['data'][0]['orderId']
check('existing order lookup matches',call(live,'/orders/'+existing)==call(module,'/orders/'+existing))
missing=str(uuid.uuid4())
check('missing order lookup matches',call(live,'/orders/'+missing)==call(module,'/orders/'+missing))
for trip in ('D1345','G1234','unknown'):
    path='/foods/2026-10-03/Shang%20Hai/Su%20Zhou/'+trip
    check('food menu '+trip+' matches',call(live,path)==call(module,path))
check('short trip rejected',call(live,'/foods/2026-10-03/Shang%20Hai/Su%20Zhou/x')==
      call(module,'/foods/2026-10-03/Shang%20Hai/Su%20Zhou/x'))

before=queue_count('food_delivery_candidate')
live_before=queue_count('food_delivery')
for label,base in [('legacy',legacy),('module',module)]:
    order_id=str(uuid.uuid4())
    body={'orderId':order_id,'foodType':2,'stationName':'suzhou',
          'storeName':'Roman Holiday','foodName':'Bone Soup','price':2.5}
    status,created=call(base,'/orders','POST',body)
    check(label+' creates food order',status==200 and created['status']==1 and
          created['data']['orderId']==order_id and created['data']['stationName']=='suzhou')
    record_id=created['data']['id']
    check(label+' reads created order',call(base,'/orders/'+order_id)[1]['data']['id']==record_id)
    check(label+' rejects duplicate order',call(base,'/orders','POST',body)[1]['status']==0)
    changed=dict(body,id=record_id,foodType=1,stationName='shanghai',
                 storeName='KFC',foodName='Hamburger',price=5.0)
    status,updated=call(base,'/orders','PUT',changed)
    check(label+' updates order',status==200 and updated['status']==1 and
          updated['data']['foodName']=='Hamburger' and updated['data']['storeName']=='KFC')
    status,deleted=call(base,'/orders/'+order_id,'DELETE')
    check(label+' deletes order',status==200 and deleted['status']==1)
    check(label+' reports deleted order missing',call(base,'/orders/'+order_id)[1]['status']==0)
check('module published one isolated delivery message',
      queue_count('food_delivery_candidate')==before+1)
check('live delivery queue unchanged by candidates',queue_count('food_delivery')==live_before)
output=root/'ts-modulith/target/evidence/food-candidate.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Food candidate comparison passed')
