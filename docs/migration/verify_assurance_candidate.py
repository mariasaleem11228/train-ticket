"""Compare Assurance's deployed API with an isolated Mongo-backed module."""
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:18888'
module='http://127.0.0.1:18114'
prefix='/api/v1/assuranceservice'
user=test_token('ROLE_USER')
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',token=user):return request(base,prefix+path,method,token=token)
def pair(path,method='GET'):
    a,b=call(legacy,path,method),call(module,path,method)
    check(method+' '+path+' matches',a==b)
    return a,b

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('23 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'assurance'})
check('Assurance has no module dependencies',graph['assurance']['dependencies']==[])
pair('/welcome')
check('unauthenticated access denied',request(legacy,prefix+'/welcome')[0]==403 and request(module,prefix+'/welcome')[0]==403)
check('admin role denied',call(legacy,'/welcome',token=test_token())[0]==403 and call(module,'/welcome',token=test_token())[0]==403)
pair('/assurances/types')
legacy_all,module_all=pair('/assurances')
check('all preexisting assurances preserved',legacy_all[1]['status']==1 and len(legacy_all[1]['data'])==len(module_all[1]['data']))
first=legacy_all[1]['data'][0]
pair('/assurances/assuranceid/'+first['id'])
pair('/assurance/orderid/'+first['orderId'])
missing=str(uuid.uuid4())
pair('/assurances/assuranceid/'+missing)
pair('/assurance/orderid/'+missing)
pair('/assurances/99/'+missing)
pair('/assurances/1/'+first['orderId'])
check('invalid type did not create record',call(module,'/assurance/orderid/'+missing)[1]['status']==0)
check('existing order unchanged',call(module,'/assurances/assuranceid/'+first['id'])[1]['data']['orderId']==first['orderId'])

# A synthetic order exercises the write path in the isolated candidate only.
candidate_order=str(uuid.uuid4())
try:
    status,created=call(module,'/assurances/1/'+candidate_order)
    check('candidate creates insurance',status==200 and created['status']==1 and created['data']['orderId']==candidate_order)
    assurance_id=created['data']['id']
    check('duplicate create rejected',call(module,'/assurances/1/'+candidate_order)[1]['msg']=='Fail.Assurance already exists')
    check('candidate lookup by order',call(module,'/assurance/orderid/'+candidate_order)[1]['data']['id']==assurance_id)
    check('candidate modify',call(module,'/assurances/'+assurance_id+'/'+candidate_order+'/1','PATCH')[1]['msg']=='Modify Success')
    check('candidate delete by id',call(module,'/assurances/assuranceid/'+assurance_id,'DELETE')[1]['status']==1)
    check('deleted record absent',call(module,'/assurance/orderid/'+candidate_order)[1]['status']==0)
finally:
    call(module,'/assurances/orderid/'+candidate_order,'DELETE')

output=root/'ts-modulith/target/evidence/assurance-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Assurance comparison passed')
