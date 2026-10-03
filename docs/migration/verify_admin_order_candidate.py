"""Compare live read contracts and exercise Admin Order writes on isolated copies."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:16112'
new = 'http://127.0.0.1:18126'
prefix = '/api/v1/adminorderservice'
admin = test_token('ROLE_ADMIN')
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def call(base,path,method='GET',body=None,token=admin):
    return request(base,prefix+path,method,body,token)

wait_ready(new,'/actuator/health')
for path in ('/welcome','/adminorder'):
    for role in (None,'ROLE_USER','ROLE_ADMIN'):
        token = test_token(role) if role else None
        legacy = call(old,path,token=token)
        module = call(new,path,token=token)
        expected = 200 if role == 'ROLE_ADMIN' else 403
        check((role or 'anonymous')+' '+path+' matches legacy',
              legacy[0] == module[0] == expected and
              (expected != 200 or legacy[1] == module[1]))

status, modules = request(new,'/actuator/modulith')
check('35 modules and two order dependencies',status == 200 and len(modules) == 35 and
      {edge['target'] for edge in modules['adminorder']['dependencies']} == {'orders','orderother'})

before = len(call(new,'/adminorder')[1]['data'])
for kind in ('G','Z'):
    train = kind+str(uuid.uuid4().int)[:9]
    payload = {'accountId':str(uuid.uuid4()),'boughtDate':1800000000000,
               'travelDate':1800057600000,'travelTime':1800082800000,
               'contactsName':'Migration Test','documentType':1,
               'contactsDocumentNumber':'MIGRATION-ONLY','trainNumber':train,
               'coachNumber':1,'seatClass':2,'seatNumber':'5','from':'shanghai',
               'to':'taiyuan','status':0,'price':'100.0'}
    check(kind+' user cannot create',call(new,'/adminorder','POST',payload,
          test_token('ROLE_USER'))[0] == 403)
    status,created = call(new,'/adminorder','POST',payload)
    check(kind+' create',status == 200 and created['status'] == 1 and
          created['data']['trainNumber'] == train)
    current = call(new,'/adminorder')[1]['data']
    check(kind+' appears in combined list',len(current) == before+1 and
          any(row['trainNumber'] == train for row in current))
    updated = dict(created['data'],price='125.0')
    status,modified = call(new,'/adminorder','PUT',updated)
    check(kind+' update',status == 200 and modified['status'] == 1 and
          modified['data']['price'] == '125.0')
    status,deleted = call(new,'/adminorder/'+str(created['data']['id'])+'/'+train,'DELETE')
    check(kind+' delete',status == 200 and deleted['status'] == 1)
    check(kind+' removed',len(call(new,'/adminorder')[1]['data']) == before)

output = root/'ts-modulith/target/evidence/admin-order-candidate.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Admin Order candidate comparison passed')
