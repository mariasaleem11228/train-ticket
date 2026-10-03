"""Compare User reads and exercise isolated User-to-Auth writes."""
import json
import uuid
from pathlib import Path

from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:12342'
module='http://127.0.0.1:18122'
prefix='/api/v1/userservice/users'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('31 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'user'})
check('User uses published Auth API',
      {edge['target'] for edge in graph['user']['dependencies']}=={'auth'})

for path,label in (('/hello','welcome'),('','all users'),('/fdse_microservice','by name'),
                   ('/id/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f','by ID'),
                   ('/not-a-user','missing name'),
                   ('/id/00000000-0000-0000-0000-000000000000','missing ID')):
    left=request(legacy,prefix+path)
    right=request(module,prefix+path)
    if path=='':
        left=(left[0],{**left[1],'data':sorted(left[1]['data'],key=lambda x:x['userId'])})
        right=(right[0],{**right[1],'data':sorted(right[1]['data'],key=lambda x:x['userId'])})
    check(label+' matches deployed User',left==right)

uid=str(uuid.uuid4());name='migration_user_'+uid[:8]
payload={'userId':uid,'userName':name,'password':'candidate-only-password',
         'gender':1,'documentType':1,'documentNum':'candidate-document','email':'candidate@example.test'}
status,body=request(module,prefix+'/register','POST',payload)
check('isolated registration returns deployed shape',status==201 and body['status']==1 and
      body['msg']=='REGISTER USER SUCCESS' and body['data']==payload)
status,body=request(module,prefix+'/'+name)
check('isolated User profile is readable',status==200 and body['data']==payload)
status,body=request(module,'/api/v1/users/login','POST',
                    {'username':name,'password':payload['password'],'verificationCode':''})
check('registration creates Auth credentials locally',status==200 and body['status']==1 and
      body['data']['userId']==uid)
status,body=request(module,prefix+'/register','POST',payload)
check('duplicate name is rejected',status==201 and body==
      {'status':0,'msg':'USER HAS ALREADY EXISTS','data':None})
updated={**payload,'email':'changed@example.test','documentNum':'changed-document'}
status,body=request(module,prefix,'PUT',updated)
check('isolated profile update',status==200 and body['status']==1 and
      body['msg']=='SAVE USER SUCCESS' and body['data']==updated)
check('updated profile is readable',request(module,prefix+'/id/'+uid)[1]['data']==updated)
status,body=request(module,prefix+'/'+uid,'DELETE',token=test_token('ROLE_ADMIN'))
check('isolated deletion returns deployed envelope',status==200 and body==
      {'status':1,'msg':'DELETE SUCCESS','data':None})
check('deletion removes User profile',request(module,prefix+'/id/'+uid)[1]['status']==0)
status,body=request(module,'/api/v1/users/login','POST',
                    {'username':name,'password':payload['password'],'verificationCode':''})
check('deletion removes Auth credentials',status==200 and body['status']==0)

output=root/'ts-modulith/target/evidence/user-candidate.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('User candidate comparison passed')
