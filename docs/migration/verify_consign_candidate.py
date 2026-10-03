"""Compare deployed Consign reads and isolated create/update flows."""
import json
import uuid
from pathlib import Path
from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
live='http://127.0.0.1:16111'
legacy='http://127.0.0.1:26111'
module='http://127.0.0.1:18116'
prefix='/api/v1/consignservice'
token=test_token('ROLE_USER')
checks=[]
def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)
def call(base,path,method='GET',body=None,auth=token):return request(base,prefix+path,method,body,auth)
def pair(a,b,path):
    left,right=call(a,path),call(b,path)
    check('GET '+path+' matches',left==right)
    return left

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('25 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'consign'})
check('Consign uses published ConsignPrice API',
      {edge['target'] for edge in graph['consign']['dependencies']}=={'consignprice'})
pair(live,module,'/welcome')
check('unauthenticated welcome denied',call(live,'/welcome',auth=None)[0]==403 and
      call(module,'/welcome',auth=None)[0]==403)
check('admin role permitted',call(live,'/welcome',auth=test_token())==call(module,'/welcome',auth=test_token()))
existing_order='19f7808b-cd82-4cf7-9f6b-5c8135912fa8'
existing_account='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f'
pair(live,module,'/consigns/order/'+existing_order)
pair(live,module,'/consigns/account/'+existing_account)
pair(live,module,'/consigns/23')
missing=str(uuid.uuid4())
pair(live,module,'/consigns/order/'+missing)
pair(live,module,'/consigns/account/'+missing)
pair(live,module,'/consigns/migration-consignee-none')

for label,base in [('legacy',legacy),('module',module)]:
    order=str(uuid.uuid4());account=str(uuid.uuid4());marker='migration-'+uuid.uuid4().hex
    body={'orderId':order,'accountId':account,'handleDate':'2026-10-02',
          'targetDate':'2026-10-03','from':'Shang Hai','to':'Su Zhou',
          'consignee':marker,'phone':'1234567890','weight':3.0,'isWithin':False}
    status,created=call(base,'/consigns','POST',body)
    check(label+' creates with local price',status==200 and created['status']==1 and
          created['data']['price']==16.0 and created['data']['orderId']==order)
    ident=created['data']['id']
    check(label+' reads new order',call(base,'/consigns/order/'+order)[1]['data']['id']==ident)
    check(label+' reads new account',len(call(base,'/consigns/account/'+account)[1]['data'])==1)
    check(label+' reads consignee',len(call(base,'/consigns/'+marker)[1]['data'])==1)
    same=dict(body,id=ident,phone='9999999999')
    status,updated=call(base,'/consigns','PUT',same)
    check(label+' updates without changing price',status==200 and updated['msg']=='Update consign success'
          and updated['data']['price']==16.0 and updated['data']['phone']=='9999999999')
    changed=dict(same,weight=4.0)
    status,updated=call(base,'/consigns','PUT',changed)
    check(label+' requotes changed weight',status==200 and updated['data']['price']==20.0)
    check(label+' retains order association',call(base,'/consigns/order/'+order)[1]['data']['id']==ident)
output=root/'ts-modulith/target/evidence/consign-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Consign comparison passed')
