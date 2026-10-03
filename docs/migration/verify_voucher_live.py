"""Create one derived Voucher from an existing synthetic order, then reuse it."""
import json
import urllib.request
from pathlib import Path
from http_support import request

root = Path(__file__).resolve().parents[2]
state = json.loads((root/'deployment/migration/.state/voucher-routing-state.json').read_text())
if state['mode'] != 'module': raise RuntimeError('Voucher must be serving from module')
status,orders = request('http://127.0.0.1:12031','/api/v1/orderservice/order')
if status != 200 or orders['status'] != 1: raise RuntimeError('Orders unavailable')
order = next(row for row in orders['data'] if row['contactsName'] == 'Migration Test' and
             row['trainNumber'].startswith(('G','D')) and row['travelTime'] is not None)
payload = {'orderId':order['id'],'type':1}

def call():
    req = urllib.request.Request('http://127.0.0.1:8080/getVoucher',
          data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.status,response.headers.get('X-Voucher-Backend'),json.load(response)

first = call()
second = call()
if first != second or first[0] != 200 or first[1] != 'module' or first[2]['order_id'] != order['id']:
    raise AssertionError((first,second))
fixture = root/'deployment/migration/.state/e2e/voucher.json'
fixture.parent.mkdir(parents=True,exist_ok=True)
fixture.write_text(json.dumps(payload,indent=2),encoding='utf-8')
print('PASS synthetic voucher created and reused through UI route:',order['id'])
