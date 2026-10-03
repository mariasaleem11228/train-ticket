"""Compare deployed Execute and isolated module status transitions on synthetic orders."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
legacy='http://127.0.0.1:12386'
candidate='http://127.0.0.1:18109'
results=[]

def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

check('candidate has eighteen business modules',
      set(request(candidate,'/actuator/modulith')[1]) ==
      set(json.loads((root/'deployment/migration/.state/hybrid.json').read_text())['modules'])|{'execute'})
check('welcome matches deployed Execute',
      request(legacy,'/api/v1/executeservice/welcome',token=test_token()) ==
      request(candidate,'/api/v1/executeservice/welcome',token=test_token()))

for label,source_port,source_path,source_id,create_path in (
        ('Orders',12031,'/api/v1/orderservice/order/',fixture['testOrders'][-1]['id'],
         '/api/v1/orderservice/order'),
        ('OrderOther',12032,'/api/v1/orderOtherService/orderOther/',
         fixture['testOtherOrders'][-1]['id'],'/api/v1/orderOtherService/orderOther')):
    status,source=request(f'http://127.0.0.1:{source_port}',source_path+source_id,token=test_token())
    check(label+' source fixture is cancelled',status==200 and source['status']==1
          and source['data']['status']==4)
    responses={}
    for target_name,target in (('legacy',legacy),('module',candidate)):
        order_host=f'http://127.0.0.1:{source_port}' if target_name=='legacy' else candidate
        order=dict(source['data'])
        order.pop('id',None)
        order['accountId']=str(uuid.uuid4())
        order['trainNumber']='MIGEXEC'+uuid.uuid4().hex[:8]
        order['status']=1
        status,created=request(order_host,create_path,'POST',order,test_token())
        check(label+' '+target_name+' synthetic order created',status==200 and created['status']==1)
        ident=created['data']['id']
        responses[target_name]=[]
        for action,expected_state in (('collected',2),('execute',6),('execute',6)):
            status,result=request(target,f'/api/v1/executeservice/execute/{action}/{ident}',token=test_token())
            responses[target_name].append((status,result))
            current=request(order_host,source_path+ident,token=test_token())
            check(label+' '+target_name+' '+action+' state',current[0]==200
                  and current[1]['status']==1 and current[1]['data']['status']==expected_state)
    check(label+' Execute responses match deployed service',
          responses['legacy']==responses['module'])

output=root/'ts-modulith/target/evidence/execute-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Execute candidate comparison passed')
