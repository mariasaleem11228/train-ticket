"""Compare deployed Auth and isolated module without changing live identities."""
import base64
import hashlib
import hmac
import json
import time
import uuid
from pathlib import Path

from http_support import request,test_token

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:12340'
module='http://127.0.0.1:18121'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def jwt_payload(token):
    header,payload,signature=token.split('.')
    raw=base64.urlsafe_b64decode(payload+'='*(-len(payload)%4))
    expected=base64.urlsafe_b64encode(hmac.new(b'secret',(header+'.'+payload).encode(),hashlib.sha256).digest()).rstrip(b'=').decode()
    if not hmac.compare_digest(signature,expected):raise AssertionError('JWT signature')
    return json.loads(raw)

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('30 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'auth'})
check('Auth is independent',graph['auth']['dependencies']==[])

for base,label in ((legacy,'legacy'),(module,'module')):
    status,body=request(base,'/api/v1/auth/hello')
    check(label+' welcome',status==200 and body=='hello')
    status,body=request(base,'/api/v1/users/login','POST',
                        {'username':'fdse_microservice','password':'WRONG','verificationCode':''})
    check(label+' rejects wrong password',status==200 and body==
          {'status':0,'msg':'Incorrect username or password.','data':None})
    status,body=request(base,'/api/v1/users/login','POST',
                        {'username':'fdse_microservice','password':'111111','verificationCode':'WRONG'})
    check(label+' login with deployed CAPTCHA response',status==200 and body.get('status')==1 and
          body.get('msg')=='login success' and body['data']['userId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f')
    claims=jwt_payload(body['data']['token'])
    check(label+' issues compatible signed JWT',claims.get('sub')=='fdse_microservice' and
          claims.get('id')=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f' and
          claims.get('roles')==['ROLE_USER'] and 3500<=claims['exp']-claims['iat']<=3700)
    check(label+' token accepted by shared host',request('http://127.0.0.1:18080',
          '/api/v1/paymentservice/welcome',token=body['data']['token'])[0]==200)
    check(label+' denies anonymous list',request(base,'/api/v1/users')[0] in (401,403))
    status,rows=request(base,'/api/v1/users',token=test_token('ROLE_ADMIN'))
    check(label+' admin lists existing identities',status==200 and
          {'fdse_microservice','admin'}<={row['username'] for row in rows} and
          all({'userId','username','password','roles','authorities'}<=set(row) for row in rows))
    status,_=request(base,'/api/v1/users',token=test_token('ROLE_USER'))
    check(label+' user role cannot list identities',status==403)

uid=str(uuid.uuid4());name='migration_auth_'+uid[:8]
payload={'userId':uid,'userName':name,'password':'candidate-only-password'}
status,body=request(module,'/api/v1/auth','POST',payload)
check('isolated registration returns legacy envelope',status==201 and body==
      {'status':1,'msg':'SUCCESS','data':payload})
status,body=request(module,'/api/v1/users/login','POST',
                    {'username':name,'password':payload['password'],'verificationCode':''})
check('isolated registered identity can log in',status==200 and body.get('status')==1 and
      body['data']['userId']==uid)
status,body=request(module,'/api/v1/users/'+uid,'DELETE',token=test_token('ROLE_ADMIN'))
check('isolated admin can delete identity',status==200 and body==
      {'status':1,'msg':'DELETE USER SUCCESS','data':None})
status,body=request(module,'/api/v1/users/login','POST',
                    {'username':name,'password':payload['password'],'verificationCode':''})
check('deleted isolated identity cannot log in',status==200 and body['status']==0)

output=root/'ts-modulith/target/evidence/auth-candidate.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Auth candidate comparison passed')
