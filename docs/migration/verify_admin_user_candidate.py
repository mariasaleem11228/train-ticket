"""Compare Admin User contracts and exercise isolated User/Auth writes."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:16115'
new = 'http://127.0.0.1:18127'
prefix = '/api/v1/adminuserservice/users'
admin = test_token('ROLE_ADMIN')
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def call(base,path='',method='GET',body=None,token=admin):
    return request(base,prefix+path,method,body,token)

wait_ready(new,'/actuator/health')
for path in ('/welcome',''):
    for role in (None,'ROLE_USER','ROLE_ADMIN'):
        token = test_token(role) if role else None
        legacy = call(old,path,token=token)
        module = call(new,path,token=token)
        expected = 200 if role == 'ROLE_ADMIN' else 403
        check((role or 'anonymous')+' '+(path or 'list')+' matches legacy',
              legacy[0] == module[0] == expected and
              (expected != 200 or legacy[1] == module[1]))

status, modules = request(new,'/actuator/modulith')
check('36 modules and published User dependency',status == 200 and len(modules) == 36 and
      {edge['target'] for edge in modules['adminuser']['dependencies']} == {'user'})

before = len(call(new)[1]['data'])
uid = str(uuid.uuid4())
name = 'admin_candidate_'+uid[:8]
payload = {'userId':uid,'userName':name,'password':'candidate-password',
           'gender':1,'documentType':1,'documentNum':'candidate-document',
           'email':'candidate@example.test'}
check('USER role cannot create',call(new,method='POST',body=payload,
      token=test_token('ROLE_USER'))[0] == 403)
status,created = call(new,method='POST',body=payload)
check('admin creates isolated user',status == 200 and created['status'] == 1 and
      created['data'] == payload)
status,listed = call(new)
check('new user appears in admin list',status == 200 and len(listed['data']) == before+1 and
      any(row['userId'] == uid for row in listed['data']))
status,login = request(new,'/api/v1/users/login','POST',
                       {'username':name,'password':payload['password'],'verificationCode':''})
check('admin creation also creates Auth credentials',status == 200 and
      login['status'] == 1 and login['data']['userId'] == uid)
status,duplicate = call(new,method='POST',body=payload)
check('duplicate user is rejected',status == 200 and duplicate ==
      {'status':0,'msg':'Add user error','data':None})
updated = dict(payload,email='changed@example.test',documentNum='changed-document')
status,modified = call(new,method='PUT',body=updated)
check('admin updates isolated user',status == 200 and modified['status'] == 1 and
      modified['data'] == updated)
check('updated user appears in admin list',any(row == updated for row in call(new)[1]['data']))
status,deleted = call(new,'/'+uid,'DELETE')
check('admin deletes isolated user',status == 200 and deleted ==
      {'status':1,'msg':'DELETE SUCCESS','data':None})
check('user list returns to baseline size',len(call(new)[1]['data']) == before)
check('Auth credentials removed',request(new,'/api/v1/users/login','POST',
      {'username':name,'password':payload['password'],'verificationCode':''})[1]['status'] == 0)
status,missing = call(new,'/'+uid,'DELETE')
check('missing user deletion uses legacy envelope',status == 200 and missing ==
      {'status':0,'msg':'delete user error','data':None})

output = root/'ts-modulith/target/evidence/admin-user-candidate.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Admin User candidate comparison passed')
