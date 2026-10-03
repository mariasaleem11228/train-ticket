"""Compare the Boot 3.5/Spring Modulith candidate with the active host.

Both hosts read the same live databases. The candidate has all writes disabled.
"""
import json
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
old='http://127.0.0.1:18080'
new='http://127.0.0.1:18086'
token=test_token()
checks=[]

def normalized(value):
    if isinstance(value,dict):return {key:normalized(item) for key,item in value.items()}
    if isinstance(value,list):
        result=[normalized(item) for item in value]
        if result and isinstance(result[0],dict) and 'id' in result[0]:result.sort(key=lambda item:item['id'])
        return result
    return value

def compare(label,path,method='GET',body=None):
    previous=request(old,path,method,body,token)
    candidate=request(new,path,method,body,token)
    passed=previous[0]==candidate[0] and normalized(previous[1])==normalized(candidate[1])
    checks.append({'step':label,'passed':passed,'old_status':previous[0],'candidate_status':candidate[0]})
    print('PASS' if passed else 'FAIL',label,flush=True)
    if not passed:raise AssertionError((label,previous,candidate))

station='/api/v1/stationservice/stations'
compare('Station full list',station)
compare('Station ID to name batch',station+'/namelist','POST',['shanghai','missing'])
normal='/api/v1/orderservice/order'
other='/api/v1/orderOtherService/orderOther'
query={'loginId':fixture['userId'],'enableStateQuery':False,
       'enableTravelDateQuery':False,'enableBoughtDateQuery':False}
for name,prefix in [('Orders',normal),('OrderOther',other)]:
    compare(name+' all records',prefix)
    compare(name+' account query',prefix+'/query','POST',query)
    compare(name+' Station refresh',prefix+'/refresh','POST',query)
    order=fixture['testOrders'][0] if name=='Orders' else fixture['testOtherOrders'][0]
    compare(name+' retained booking',prefix+'/'+order['id'])
    compare(name+' retained price',prefix+'/price/'+order['id'])
    before=request(old,prefix+'/'+order['id'],token=token)
    status,_=request(new,prefix+'/orderPay/'+order['id'],token=token)
    unchanged=before==request(old,prefix+'/'+order['id'],token=token)
    checks.append({'step':name+' candidate rejects write','passed':status==503 and unchanged})
    assert status==503 and unchanged,(name,status,unchanged)
    print('PASS',name+' candidate rejects write',flush=True)

status,health=request(new,'/actuator/health')
checks.append({'step':'candidate health','passed':status==200 and health['status']=='UP'})
assert status==200 and health['status']=='UP'
(root/'ts-modulith/target/evidence/spring-modulith-candidate.json').write_text(json.dumps(checks,indent=2))
print('Candidate checks:',len(checks),'passed')
