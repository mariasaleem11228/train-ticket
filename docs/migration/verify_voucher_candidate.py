"""Compare deployed Python Voucher with Java Voucher on isolated MySQL copies."""
import json
import urllib.error
import urllib.request
from pathlib import Path
from http_support import request, test_token, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:26101'
new = 'http://127.0.0.1:18128'
results = []

def check(label, passed):
    results.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed: raise AssertionError(label)

def post(base,payload):
    return request(base,'/getVoucher','POST',payload)

wait_ready(new,'/actuator/health')
status, graph = request(new,'/actuator/modulith')
check('37 modules and local order dependencies',status == 200 and len(graph) == 37 and
      {edge['target'] for edge in graph['voucher']['dependencies']} == {'orders','orderother'})

status,orders = request('http://127.0.0.1:12031','/api/v1/orderservice/order')
check('live Orders catalogue available',status == 200 and orders['status'] == 1)
status,others = request('http://127.0.0.1:12032','/api/v1/orderOtherService/orderOther')
check('live OrderOther catalogue available',status == 200 and others['status'] == 1)
fast = next(row for row in orders['data'] if row['travelTime'] is not None)
ordinary = next(row for row in others['data'] if row['travelTime'] is not None)
for name,order,kind in (('fast',fast,1),('ordinary',ordinary,0)):
    payload = {'orderId':order['id'],'type':kind}
    legacy = post(old,payload)
    module = post(new,payload)
    check(name+' voucher matches deployed service',legacy == module and
          legacy[0] == 200 and legacy[1]['order_id'] == order['id'])
    check(name+' voucher is reused on repeat request',post(old,payload) == legacy and
          post(new,payload) == module)
    wrong_type = dict(payload,type=1-kind)
    check(name+' existing voucher ignores type',post(old,wrong_type) == legacy and
          post(new,wrong_type) == module)

check('GET remains unsupported',request(old,'/getVoucher')[0] == 405 and
      request(new,'/getVoucher')[0] == 405)

output = root/'ts-modulith/target/evidence/voucher-candidate.json'
output.write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Voucher candidate comparison passed')
