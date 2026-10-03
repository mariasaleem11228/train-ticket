"""Exercise and remove one synthetic live User/Auth registration."""
import json
import secrets
import uuid
import urllib.request
from pathlib import Path

from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
base='http://127.0.0.1:12342'
prefix='/api/v1/userservice/users'
id=str(uuid.uuid4())
name='migration_live_'+id[:8]
password=secrets.token_urlsafe(24)
payload={'userId':id,'userName':name,'password':password,'gender':0,
         'documentType':0,'documentNum':'migration-test','email':'migration@example.test'}
checks=[]
created=False

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

try:
    with urllib.request.urlopen(urllib.request.Request(base+prefix+'/register',
        data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},
        method='POST'),timeout=20) as response:
        body=json.load(response)
        created=body.get('status')==1
        check('live User registration reaches module',response.status==201 and created and
              response.headers.get('X-User-Backend')=='module')
    status,body=request(base,prefix+'/id/'+id)
    check('live User profile created',status==200 and body.get('status')==1 and
          body['data']['userName']==name)
    status,body=request('http://127.0.0.1:12340','/api/v1/users/login','POST',
                        {'username':name,'password':password,'verificationCode':''})
    check('live Auth credentials created',status==200 and body.get('status')==1 and
          body['data']['userId']==id)
finally:
    status,current=request(base,prefix+'/id/'+id)
    if status==200 and current.get('status')==1:
        status,body=request(base,prefix+'/'+id,'DELETE',token=test_token('ROLE_ADMIN'))
        check('synthetic identity removed',status==200 and body.get('status')==1)
    # Also remove a possible Auth-only record if User persistence failed after Auth creation.
    request('http://127.0.0.1:12340','/api/v1/users/'+id,'DELETE',
            token=test_token('ROLE_ADMIN'))
if created:
    check('User profile absent after cleanup',request(base,prefix+'/id/'+id)[1]['status']==0)
    status,body=request('http://127.0.0.1:12340','/api/v1/users/login','POST',
                        {'username':name,'password':password,'verificationCode':''})
    check('Auth credentials absent after cleanup',status==200 and body.get('status')==0)
output=root/'ts-modulith/target/evidence/user-live-registration.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Live User registration and cleanup passed')
