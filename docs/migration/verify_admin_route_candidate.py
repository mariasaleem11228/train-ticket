"""Check deployed Admin Route contracts and isolated module writes."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:16113'
new = 'http://127.0.0.1:18124'
prefix = '/api/v1/adminrouteservice'
admin = test_token('ROLE_ADMIN')
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def call(base, path, method='GET', body=None, token=admin):
    return request(base,prefix+path,method,body,token)

wait_ready(new,'/actuator/health')
for path in ('/welcome','/adminroute'):
    for role in (None,'ROLE_USER','ROLE_ADMIN'):
        token = test_token(role) if role else None
        legacy = call(old,path,token=token)
        module = call(new,path,token=token)
        expected = 200 if role == 'ROLE_ADMIN' else 403
        check((role or 'anonymous')+' '+path+' matches legacy',
              legacy[0] == module[0] == expected and
              (expected != 200 or legacy[1] == module[1]))

status, modules = request(new,'/actuator/modulith')
check('33 modules and Route dependency',status == 200 and len(modules) == 33 and
      {edge['target'] for edge in modules['adminroute']['dependencies']} == {'route'})

path = '/adminroute'
payload = {'stationList':'nanjing,shanghai','distanceList':'0,250',
           'startStation':'nanjing','endStation':'shanghai'}
check('user cannot create route',call(new,path,'POST',payload,test_token('ROLE_USER'))[0] == 403)
check('anonymous cannot delete route',call(new,path+'/'+str(uuid.uuid4()),'DELETE',token=None)[0] == 403)
bad = dict(payload,distanceList='0')
legacy = call(old,path,'POST',bad)
module = call(new,path,'POST',bad)
check('invalid distance list matches legacy',legacy == module and legacy[1]['status'] == 0)

before = call(new,path)[1]['data']
status, created = call(new,path,'POST',payload)
check('create route',status == 200 and created['status'] == 1 and created['msg'] == 'Save Success')
id = created['data']['id']
check('route appears in isolated catalogue',len(call(new,path)[1]['data']) == len(before)+1)
update = dict(payload,id=id,distanceList='0,251')
status, modified = call(new,path,'POST',update)
check('modify route',status == 200 and modified['status'] == 1 and
      modified['msg'] == 'Modify success' and modified['data']['distances'] == [0,251])
status, deleted = call(new,path+'/'+id,'DELETE')
check('delete route',status == 200 and deleted['status'] == 1 and deleted['data'] == id)
check('route removed from isolated catalogue',len(call(new,path)[1]['data']) == len(before))

output = root/'ts-modulith/target/evidence/admin-route-candidate.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Admin Route candidate comparison passed')
