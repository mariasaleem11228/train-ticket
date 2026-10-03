"""Compare deployed ConsignPrice reads and isolated configuration writes."""
import json
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
live='http://127.0.0.1:16110'
legacy='http://127.0.0.1:26110'
module='http://127.0.0.1:18115'
prefix='/api/v1/consignpriceservice'
token=test_token()
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',body=None,auth=token):return request(base,prefix+path,method,body,auth)
def compare(a,b,path):
    result_a,result_b=call(a,path),call(b,path)
    check(path+' matches',result_a==result_b)
    return result_a

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('24 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'consignprice'})
check('ConsignPrice has no module dependencies',graph['consignprice']['dependencies']==[])
compare(live,module,'/welcome')
check('unauthenticated welcome denied',call(live,'/welcome',auth=None)[0]==403 and call(module,'/welcome',auth=None)[0]==403)
compare(live,module,'/consignprice/config')
compare(live,module,'/consignprice/price')
for weight in ('0','0.5','1','1.01','2','10'):
    for region in ('true','false'):
        compare(live,module,'/consignprice/'+weight+'/'+region)
check('user role permitted',call(live,'/consignprice/2/true',auth=test_token('ROLE_USER'))==
      call(module,'/consignprice/2/true',auth=test_token('ROLE_USER')))

# Both writes are directed to disposable databases copied from the live snapshot.
left=call(legacy,'/consignprice/config')[1]['data']
right=call(module,'/consignprice/config')[1]['data']
check('isolated legacy and module start from same config',left==right)
changed=dict(left,initialWeight=2.0,initialPrice=9.0,withinPrice=2.5,beyondPrice=5.0)
response_a=call(legacy,'/consignprice','POST',changed)
response_b=call(module,'/consignprice','POST',changed)
check('isolated configuration update matches',response_a==response_b)
compare(legacy,module,'/consignprice/config')
compare(legacy,module,'/consignprice/price')
compare(legacy,module,'/consignprice/1/true')
compare(legacy,module,'/consignprice/3/true')
compare(legacy,module,'/consignprice/3/false')
output=root/'ts-modulith/target/evidence/consign-price-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ConsignPrice comparison passed')
