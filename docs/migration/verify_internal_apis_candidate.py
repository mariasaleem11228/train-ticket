"""Start an isolated host and exercise direct APIs with legacy URLs disabled."""
import datetime
import json
import random
import time
from pathlib import Path

import hybrid_routing as routing
from http_support import request, test_token, wait_ready

name = 'internal-apis-full-candidate'
base = 'http://127.0.0.1:18147'
existing = routing.docker('ps', '-a', '--format', '{{.Names}}').splitlines()
if name in existing:
    raise RuntimeError(name + ' already exists; inspect it before replacing it')

host = json.loads(routing.docker('inspect', 'station-migration-modulith-1'))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
database = 'internal_apis_candidate_' + str(int(time.time()))
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
for key in ('AUTH_VERIFY_URL', 'CANCEL_USER_URL',
            'PRESERVE_USER_URL', 'PRESERVE_ASSURANCE_URL', 'PRESERVE_FOOD_URL',
            'PRESERVE_CONSIGN_URL', 'PRESERVE_OTHER_USER_URL',
            'PRESERVE_OTHER_ASSURANCE_URL', 'PRESERVE_OTHER_FOOD_URL',
            'PRESERVE_OTHER_CONSIGN_URL'):
    env[key] = 'http://127.0.0.1:1'
env.update(ORDER_WRITES_ENABLED='true', PRESERVE_WRITES_ENABLED='true',
           FOOD_WRITES_ENABLED='true', ASSURANCE_WRITES_ENABLED='true',
           CONSIGN_WRITES_ENABLED='true',
           ORDER_MONGO_URI='mongodb://ts-order-mongo:27017/' + database,
           FOOD_MONGO_URI='mongodb://ts-food-mongo:27017/' + database,
           ASSURANCE_MONGO_URI='mongodb://ts-assurance-mongo:27017/' + database,
           CONSIGN_MONGO_URI='mongodb://ts-consign-mongo:27017/' + database,
           WAIT_ORDER_RETRY_ENABLED='false', MODULITH_OWNERSHIP_FILE='')
env_path = routing.ROOT / 'ts-modulith/target/internal-apis-candidate.env'
env_path.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
try:
    routing.docker('run', '-d', '--name', name, '--network', 'train-ticket_my-network',
                   '-p', '127.0.0.1:18147:18080', '--env-file', str(env_path),
                   'train-ticket/ts-modulith:internal-apis-candidate')
    wait_ready(base, '/actuator/health', seconds=180)
    status, graph = request(base, '/actuator/modulith')
    assert status == 200 and len(graph) == 44
    assert {d['target'] for d in graph['auth']['dependencies']} == {'verifycode'}
    assert {'user', 'assurance', 'food', 'consign'} <= {
        d['target'] for d in graph['preserve']['dependencies']}
    assert {'user', 'assurance', 'food', 'consign'} <= {
        d['target'] for d in graph['preserveother']['dependencies']}
    status, login = request(base, '/api/v1/users/login', 'POST', {
        'username': 'fdse_microservice', 'password': '111111',
        'verificationCode': 'WRONG'})
    assert status == 200 and login['status'] == 1, login
    fixture = json.loads((routing.STATE / 'e2e/fixture.json').read_text())
    account, contact = fixture['userId'], fixture['contactId']
    date = (datetime.datetime.now(datetime.timezone.utc) +
            datetime.timedelta(days=random.randint(7, 21))).strftime('%Y-%m-%d')
    token = test_token('ROLE_ADMIN')
    search = {'startingPlace': 'Nan Jing', 'endPlace': 'Shang Hai',
              'departureTime': date}
    status, trips = request(base, '/api/v1/travelservice/trips/left', 'POST', search, token)
    assert status == 200 and trips['status'] == 1 and trips['data'], trips
    trip = trips['data'][0]['tripId']
    if isinstance(trip, dict):
        trip = str(trip['type']) + str(trip['number'])
    body = {'accountId': account, 'contactsId': contact, 'tripId': trip,
            'seatType': 3, 'date': date, 'from': 'Nan Jing', 'to': 'Shang Hai',
            'assurance': 1, 'foodType': 1, 'foodName': 'Spicy hot noodles',
            'foodPrice': 5, 'handleDate': date, 'consigneeName': 'Migration Test',
            'consigneePhone': '123456789', 'consigneeWeight': 2, 'isWithin': True}
    status, booked = request(base, '/api/v1/preserveservice/preserve', 'POST', body, token)
    assert status == 200 and booked['status'] == 1 and booked['msg'] == 'Success.', booked
    status, orders = request(base, '/api/v1/orderservice/order', token=token)
    assert status == 200 and orders['status'] == 1, orders
    order_ids = [row['id'] for row in orders['data'] if row['accountId'] == account]
    assert len(order_ids) == 1, orders
    for api_path in ('/api/v1/assuranceservice/assurance/orderid/',
                     '/api/v1/foodservice/orders/',
                     '/api/v1/consignservice/consigns/order/'):
        status, result = request(base, api_path + order_ids[0],
                                 token=test_token('ROLE_USER', account))
        assert status == 200 and result['status'] == 1, (api_path, result)
    print('PASS internal APIs: graph, Auth, isolated Preserve booking, Assurance, Food and Consign')
finally:
    if name in routing.docker('ps', '-a', '--format', '{{.Names}}').splitlines():
        routing.docker('stop', name)
        routing.docker('rm', name)
    env_path.unlink(missing_ok=True)
