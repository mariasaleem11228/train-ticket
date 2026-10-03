"""Compare stable order fields from legacy and module Preserve bookings."""
import json
from pathlib import Path
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
fixture = json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
ids = {item['stage']: item['id'] for item in fixture['testOrders']
       if item['stage'] in ('preserve-baseline', 'preserve-module')}
assert set(ids) == {'preserve-baseline', 'preserve-module'}
orders = {}
for stage, order_id in ids.items():
    status, response = request('http://127.0.0.1:12031',
                               '/api/v1/orderservice/order/' + order_id, token=test_token())
    assert status == 200 and response['status'] == 1
    orders[stage] = response['data']
fields = ('travelDate','travelTime','accountId','contactsName','documentType',
          'contactsDocumentNumber','trainNumber','coachNumber','seatClass',
          'from','to','status','price')
results = [{'step': field, 'passed': orders['preserve-baseline'][field] ==
            orders['preserve-module'][field]} for field in fields]
for item in results:
    print(('PASS ' if item['passed'] else 'FAIL ') + item['step'])
assert all(item['passed'] for item in results)
output = root/'ts-modulith/target/evidence/preserve-orders.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'Preserve order comparison passed: {len(results)} fields')
