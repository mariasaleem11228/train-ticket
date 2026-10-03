"""Exercise the Order List cancel route through browser-facing port 8080."""
import json
import uuid
import urllib.request
from pathlib import Path

from http_support import request, test_token

root = Path(__file__).resolve().parents[2]
fixture = json.loads((root / 'deployment/migration/.state/e2e/fixture.json').read_text())
order_path = '/api/v1/orderservice/order'
status, source = request('http://127.0.0.1:12031',
                         order_path + '/' + fixture['testOrders'][-1]['id'],
                         token=test_token())
assert status == 200 and source['status'] == 1, 'Source order unavailable'
order = dict(source['data'])
order.pop('id', None)
order.update(accountId=fixture['userId'], trainNumber='D1345',
             status=1, price='250.0')
status, created = request('http://127.0.0.1:12031', order_path, 'POST',
                          order, test_token())
assert status == 200 and created['status'] == 1, 'Synthetic order creation failed'
ident = created['data']['id']
login_id = 'migration-cancel-' + uuid.uuid4().hex
base = 'http://127.0.0.1:8080/api/v1/cancelservice/cancel'


def through_ui(path):
    web = urllib.request.Request(base + path,
                                 headers={'Authorization': 'Bearer ' + test_token()})
    with urllib.request.urlopen(web, timeout=30) as response:
        assert response.status == 200, path
        assert response.headers.get('X-Cancel-Backend') == 'module', path
        return json.loads(response.read())


quoted = through_ui('/refound/' + ident)
assert quoted == {'status': 1, 'msg': 'Success. ', 'data': '200.00'}, quoted
print('PASS browser-facing refund quote uses Cancel module')
cancelled = through_ui('/' + ident + '/' + login_id)
assert cancelled == {'status': 1, 'msg': 'Success.', 'data': 'test not null'}, cancelled
print('PASS browser-facing cancellation uses Cancel module')
status, updated = request('http://127.0.0.1:12031', order_path + '/' + ident,
                          token=test_token())
assert status == 200 and updated['status'] == 1 and updated['data']['status'] == 4
status, balances = request('http://127.0.0.1:18673',
                           '/api/v1/inside_pay_service/inside_payment/account',
                           token=test_token())
assert status == 200 and any(row['userId'] == login_id and row['balance'] == '200.00'
                             for row in balances['data']), 'Refund drawback missing'
print('PASS cancelled order and refund retained')
output = root / 'ts-modulith/target/evidence/cancel-ui.json'
output.write_text(json.dumps({'orderId': ident, 'backend': 'module', 'passed': True},
                             indent=2), encoding='utf-8')
print('Cancel UI route passed')
