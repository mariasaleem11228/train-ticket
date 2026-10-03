"""Compare deployed Admin Travel behavior and exercise both isolated writers."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:16114'
new = 'http://127.0.0.1:18125'
prefix = '/api/v1/admintravelservice'
admin = test_token('ROLE_ADMIN')
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def call(base,path,method='GET',body=None,token=admin):
    return request(base,prefix+path,method,body,token)

wait_ready(new,'/actuator/health')
for path in ('/welcome','/admintravel'):
    for role in (None,'ROLE_USER','ROLE_ADMIN'):
        token = test_token(role) if role else None
        legacy = call(old,path,token=token)
        module = call(new,path,token=token)
        expected = 200 if role == 'ROLE_ADMIN' else 403
        check((role or 'anonymous')+' '+path+' matches legacy',
              legacy[0] == module[0] == expected and
              (expected != 200 or legacy[1] == module[1]))

status, modules = request(new,'/actuator/modulith')
check('34 modules and two Travel dependencies',status == 200 and len(modules) == 34 and
      {edge['target'] for edge in modules['admintravel']['dependencies']} == {'travel','travel2'})

before = len(call(new,'/admintravel')[1]['data'])
for kind in ('G','Z'):
    trip = kind+str(uuid.uuid4().int)[:9]
    payload = {'tripId':trip,'trainTypeId':kind+'aoTieOne','routeId':
               '92708982-77af-4318-be25-57ccb0ff69ad',
               'startingStationId':'nanjing','stationsId':'suzhou',
               'terminalStationId':'shanghai',
               'startingTime':1791000000000,'endTime':1791003600000}
    check(kind+' user cannot create',call(new,'/admintravel','POST',payload,
          test_token('ROLE_USER'))[0] == 403)
    status,created = call(new,'/admintravel','POST',payload)
    check(kind+' create',status == 200 and created ==
          {'status':1,'msg':'[Admin add new travel]','data':None})
    current = call(new,'/admintravel')[1]['data']
    check(kind+' appears in combined catalogue',len(current) == before+1 and
          any(row['trip']['tripId']['type'] == kind and
              row['trip']['tripId']['number'] == trip[1:] for row in current))
    updated = dict(payload,endTime=1791007200000)
    status,modified = call(new,'/admintravel','PUT',updated)
    check(kind+' update',status == 200 and modified['status'] == 1 and
          modified['data']['endTime'] == updated['endTime'])
    status,deleted = call(new,'/admintravel/'+trip,'DELETE')
    check(kind+' delete',status == 200 and deleted['status'] == 1 and deleted['data'] == trip)
    check(kind+' removed',len(call(new,'/admintravel')[1]['data']) == before)

missing = 'G'+str(uuid.uuid4().int)[:9]
legacy = call(old,'/admintravel/'+missing,'DELETE')
module = call(new,'/admintravel/'+missing,'DELETE')
check('missing delete matches legacy',legacy == module and legacy[1]['status'] == 0)

output = root/'ts-modulith/target/evidence/admin-travel-candidate.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Admin Travel candidate comparison passed')
