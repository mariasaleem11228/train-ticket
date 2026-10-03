"""Compare stable order fields from legacy and module PreserveOther bookings."""
import json
from pathlib import Path
from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
fixture = json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
ids = {item['stage']: item['id'] for item in fixture['testOtherOrders']
       if item['stage'] in ('preserve-other-baseline', 'preserve-other-module')}
assert set(ids) == {'preserve-other-baseline', 'preserve-other-module'}
orders = {}
for stage, order_id in ids.items():
    status, response = request('http://127.0.0.1:12032',
                               '/api/v1/orderOtherService/orderOther/' + order_id, token=test_token())
    assert status == 200 and response['status'] == 1
    orders[stage] = response['data']
fields = ('travelDate','travelTime','accountId','contactsName','documentType',
          'contactsDocumentNumber','trainNumber','coachNumber','seatClass',
          'from','to','status','price')
results = [{'step': field, 'passed': orders['preserve-other-baseline'][field] ==
            orders['preserve-other-module'][field]} for field in fields]
for item in results:
    print(('PASS ' if item['passed'] else 'FAIL ') + item['step'])
assert all(item['passed'] for item in results)
output = root/'ts-modulith/target/evidence/preserve-other-orders.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'PreserveOther order comparison passed: {len(results)} fields')
