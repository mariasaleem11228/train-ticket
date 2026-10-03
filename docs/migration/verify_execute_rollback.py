"""Rehearse Execute rollback and return with synthetic Orders and OrderOther transitions."""
import json
import uuid
import urllib.request
from pathlib import Path
import hybrid_routing as routing
from http_support import request, test_token

root=Path(__file__).resolve().parents[2]
fixture=json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
results=[]

def check(label,passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def backend():
    req=urllib.request.Request('http://127.0.0.1:12386/api/v1/executeservice/welcome',
                               headers={'Authorization':'Bearer '+test_token()})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-Execute-Backend'),response.read().decode()

def transitions(stage):
    for label,port,path,source_id in (
            ('Orders',12031,'/api/v1/orderservice/order',fixture['testOrders'][-1]['id']),
            ('OrderOther',12032,'/api/v1/orderOtherService/orderOther',
             fixture['testOtherOrders'][-1]['id'])):
        status,source=request(f'http://127.0.0.1:{port}',path+'/'+source_id,token=test_token())
        check(stage+' '+label+' source',status==200 and source['status']==1)
        order=dict(source['data']);order.pop('id',None)
        order['accountId']=str(uuid.uuid4())
        order['trainNumber']='MIGEXEC'+uuid.uuid4().hex[:8]
        order['status']=1
        status,created=request(f'http://127.0.0.1:{port}',path,'POST',order,test_token())
        check(stage+' '+label+' created',status==200 and created['status']==1)
        ident=created['data']['id']
        for action,expected in (('collected',2),('execute',6)):
            status,result=request('http://127.0.0.1:12386',
                                   f'/api/v1/executeservice/execute/{action}/{ident}',
                                   token=test_token())
            read_status,current=request(f'http://127.0.0.1:{port}',path+'/'+ident,token=test_token())
            check(stage+' '+label+' '+action,status==200 and result['status']==1 and
                  read_status==200 and current['status']==1 and current['data']['status']==expected)

if json.loads(routing.DEFS['execute']['file'].read_text())['mode']!='module':
    raise RuntimeError('Execute must start in module mode')
check('module serves Execute identity',backend()==(200,'module','Welcome to [ Execute Service ] !'))
try:
    routing.switch('execute','legacy')
    check('legacy serves Execute identity',backend()==(200,'legacy','Welcome to [ Execute Service ] !'))
    check('inactive module blocks mutating GET',
          request('http://127.0.0.1:18080',
                  '/api/v1/executeservice/execute/collected/'+str(uuid.uuid4()),
                  token=test_token())[0]==503)
    transitions('legacy rollback')
finally:
    if json.loads(routing.DEFS['execute']['file'].read_text())['mode']!='module':
        routing.switch('execute','module')
check('module serves Execute identity again',backend()==(200,'module','Welcome to [ Execute Service ] !'))
transitions('module return')
output=root/'ts-modulith/target/evidence/execute-rollback.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Execute rollback rehearsal passed')
