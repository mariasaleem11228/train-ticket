"""Check live WaitOrder routing, ownership, persistence, and duplicate handling."""
import uuid
import sys
import hybrid_routing as routing
from http_support import request,test_token

base='http://127.0.0.1:18080'
path='/api/v1/waitorderservice'
status,graph=request(base,'/actuator/modulith')
assert status==200 and len(graph)==45 and {d['target'] for d in graph['waitorder']['dependencies']}=={'preserve'}
assert request(base,path+'/orders')[0] in (401,403)
token=test_token('ROLE_ADMIN')
assert request(base,path+'/welcome',token=token)==(200,'Welcome to [ Wait Order Service ] !')
status,all_orders=request(base,path+'/orders',token=token)
assert status==200 and all_orders['status'] in (0,1)
status,waiting=request(base,path+'/waitlistorders',token=token)
assert status==200 and waiting['status'] in (0,1)
columns={line.split('\t',1)[0] for line in routing.docker('exec','station-migration-wait-order-mysql-1',
    'mysql','-N','-B','-uroot','-proot','waitorderservice',
    '-e','SHOW COLUMNS FROM wait_list_order').splitlines()}
assert {'next_attempt','lease_token','lease_until','booking_order_id',
        'attempt_count','last_error'} <= columns,columns
if '--write' not in sys.argv:
    print('PASS live WaitOrder: 45 modules, authorization and reads (use --write for a synthetic create check)')
    raise SystemExit(0)
account=str(uuid.uuid4())
body={'accountId':account,'contactsId':str(uuid.uuid4()),'tripId':'D1345',
      'seatType':2,'date':'2026-10-05','from':'Shang Hai','to':'Su Zhou','price':'50.0'}
status,created=request(base,path+'/order',method='POST',body=body,token=token)
assert status==200 and created['status']==1,created
status,duplicate=request(base,path+'/order',method='POST',body=body,token=token)
assert status==200 and duplicate['status']==0,duplicate
status,all_orders=request(base,path+'/orders',token=token)
assert status==200 and any(row['accountId']==account and row['trainNumber']=='D1345'
                           for row in all_orders['data'])
print('PASS live WaitOrder: 45 modules, authorization, create, duplicate and reads')
