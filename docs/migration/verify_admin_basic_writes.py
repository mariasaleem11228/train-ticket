"""Exercise every Admin Basic Info write on isolated provider snapshots."""
import json
import uuid
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:18123'
prefix = '/api/v1/adminbasicservice/adminbasic/'
admin = test_token('ROLE_ADMIN')
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed: raise AssertionError(label)

def call(name, method='GET', body=None, suffix='', token=admin):
    return request(base,prefix+name+suffix,method,body,token)

def ok(label, response):
    check(label,response[0] == 200 and response[1]['status'] == 1)
    return response[1]

wait_ready(base,'/actuator/health')
key = 'MIGADMIN-'+uuid.uuid4().hex[:8]
contact = {'accountId':str(uuid.uuid4()),'name':key,'documentType':1,
           'documentNumber':key,'phoneNumber':'0000000000'}
station = {'id':str(uuid.uuid4()),'name':key,'stayTime':3}
train = {'id':key,'economyClass':10,'confortClass':5,'averageSpeed':100}
config = {'name':key,'value':'1','description':'migration test'}
price = {'id':str(uuid.uuid4()),'trainType':key,'routeId':key,
         'basicPriceRate':1.0,'firstClassPriceRate':2.0}
records = {'contacts':contact,'stations':station,'trains':train,'configs':config,'prices':price}

for name, body in records.items():
    check(name+' rejects user write',call(name,'POST',body,token=test_token('ROLE_USER'))[0] == 403)
    ok(name+' create',call(name,'POST',body))
    catalogue = ok(name+' list after create',call(name))['data']
    identifier = 'name' if name == 'configs' else 'id'
    if name == 'contacts':
        created = next((row for row in catalogue if row['documentNumber'] == key),None)
        check(name+' persisted',created is not None)
        body = created
    else:
        check(name+' persisted',any(row[identifier] == body[identifier] for row in catalogue))
    if name == 'contacts': body = dict(body,name=key+'-updated')
    elif name == 'stations': body = dict(body,stayTime=4)
    elif name == 'trains': body = dict(body,averageSpeed=101)
    elif name == 'configs': body = dict(body,value='2')
    else: body = dict(body,basicPriceRate=1.5)
    ok(name+' update',call(name,'PUT',body))
    catalogue = ok(name+' list after update',call(name))['data']
    updated = next(row for row in catalogue if row[identifier] == body[identifier])
    field = {'contacts':'name','stations':'stayTime','trains':'averageSpeed',
             'configs':'value','prices':'basicPriceRate'}[name]
    check(name+' update persisted',updated[field] == body[field])
    if name in ('contacts','trains','configs'):
        deleted = call(name,'DELETE',suffix='/'+str(body[identifier]))
    else:
        deleted = call(name,'DELETE',body)
    ok(name+' delete',deleted)
    catalogue = ok(name+' list after delete',call(name))['data']
    check(name+' removed',not any(row[identifier] == body[identifier] for row in catalogue))

output = root/'ts-modulith/target/evidence/admin-basic-writes.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Admin Basic Info isolated write checks passed')
