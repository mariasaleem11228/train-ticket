"""Exercise the HTTP-free host with isolated booking and add-on databases."""
import datetime
import json
import random
import re
import time

import hybrid_routing as routing
from http_support import request, test_token, wait_ready

name = 'direct-modules-candidate'
base = 'http://127.0.0.1:18150'
image = 'train-ticket/ts-modulith:direct-modules-candidate'
if name in routing.docker('ps', '-a', '--format', '{{.Names}}').splitlines():
    raise RuntimeError(name + ' already exists; inspect it before replacing it')

# A source guard catches accidental reintroduction of an in-host HTTP client.
source = routing.ROOT / 'ts-modulith/src/main/java'
pattern = re.compile(r'\b(RestTemplate|WebClient|RestClient|FeignClient|HttpClient|HttpURLConnection)\b|https?://')
for path in source.rglob('*.java'):
    assert not pattern.search(path.read_text(encoding='utf-8')), path

host = json.loads(routing.docker('inspect', 'station-migration-modulith-1'))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
database = 'direct_modules_candidate_' + str(int(time.time()))
env.update(ORDER_WRITES_ENABLED='true', ORDER_OTHER_WRITES_ENABLED='true',
           PRESERVE_WRITES_ENABLED='true', PRESERVE_OTHER_WRITES_ENABLED='true',
           FOOD_WRITES_ENABLED='true', ASSURANCE_WRITES_ENABLED='true',
           CONSIGN_WRITES_ENABLED='true',
           ORDER_MONGO_URI='mongodb://ts-order-mongo:27017/' + database,
           ORDER_OTHER_MONGO_URI='mongodb://ts-order-other-mongo:27017/' + database,
           FOOD_MONGO_URI='mongodb://ts-food-mongo:27017/' + database,
           ASSURANCE_MONGO_URI='mongodb://ts-assurance-mongo:27017/' + database,
           CONSIGN_MONGO_URI='mongodb://ts-consign-mongo:27017/' + database,
           FOOD_DELIVERY_QUEUE=database,
           WAIT_ORDER_RETRY_ENABLED='false', MODULITH_OWNERSHIP_FILE='')
env_path = routing.ROOT / 'ts-modulith/target/direct-modules-candidate.env'
env_path.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
checks = []
try:
    routing.docker('run', '-d', '--name', name, '--network', 'train-ticket_my-network',
                   '-p', '127.0.0.1:18150:18080', '--env-file', str(env_path), image)
    wait_ready(base, '/actuator/health', seconds=180)
    status, graph = request(base, '/actuator/modulith')
    assert status == 200 and len(graph) == 45, (status, len(graph))
    expected = {
        'auth': {'verifycode'}, 'cancel': {'user'},
        'seat': {'orders', 'orderother', 'config', 'tripcatalog', 'route', 'train'},
        'travel': {'train', 'route', 'orders', 'seat', 'ticketinfo'},
        'travel2': {'train', 'route', 'orders', 'seat', 'ticketinfo'},
    }
    for module, dependencies in expected.items():
        actual = {item['target'] for item in graph[module]['dependencies']}
        assert dependencies <= actual, (module, actual)
    checks.append('45-module graph and local dependencies')

    status, login = request(base, '/api/v1/users/login', 'POST', {
        'username': 'fdse_microservice', 'password': '111111',
        'verificationCode': 'WRONG'})
    assert status == 200 and login['status'] == 1, login
    checks.append('Auth calls local Verification Code')

    fixture = json.loads((routing.STATE / 'e2e/fixture.json').read_text())
    account, contact = fixture['userId'], fixture['contactId']
    date = (datetime.datetime.now(datetime.timezone.utc) +
            datetime.timedelta(days=random.randint(7, 21))).strftime('%Y-%m-%d')
    token = test_token('ROLE_ADMIN')
    query = {'startingPlace': 'Nan Jing', 'endPlace': 'Shang Hai',
             'departureTime': date}
    for service, booking, orders in (
        ('travelservice', '/api/v1/preserveservice/preserve', '/api/v1/orderservice/order'),
        ('travel2service', '/api/v1/preserveotherservice/preserveOther',
         '/api/v1/orderOtherService/orderOther')):
        status, trips = request(base, '/api/v1/' + service + '/trips/left', 'POST', query, token)
        assert status == 200 and trips['status'] == 1 and trips['data'], (service, trips)
        trip = trips['data'][0]['tripId']
        number = trip if isinstance(trip, str) else str(trip['type']) + str(trip['number'])
        body = {'accountId': account, 'contactsId': contact, 'tripId': number,
                'seatType': 3, 'date': date, 'from': 'Nan Jing', 'to': 'Shang Hai',
                'assurance': 1, 'foodType': 1, 'foodName': 'Spicy hot noodles',
                'foodPrice': 5, 'handleDate': date,
                'consigneeName': 'Migration Test', 'consigneePhone': '123456789',
                'consigneeWeight': 2, 'isWithin': True}
        status, booked = request(base, booking, 'POST', body, token)
        assert status == 200 and booked['status'] == 1, (service, booked)
        status, listed = request(base, orders, token=token)
        assert status == 200 and listed['status'] == 1 and len(listed['data']) == 1, (service, listed)
        order_id = listed['data'][0]['id']
        for path in ('/api/v1/assuranceservice/assurance/orderid/',
                     '/api/v1/foodservice/orders/',
                     '/api/v1/consignservice/consigns/order/'):
            status, result = request(base, path + order_id,
                                     token=test_token('ROLE_USER', account))
            assert status == 200 and result['status'] == 1, (service, path, result)
        checks.append(service + ' booking persists with Assurance, Food and Consign')

    routing.EVIDENCE.mkdir(parents=True, exist_ok=True)
    (routing.EVIDENCE / 'direct-modules-candidate.json').write_text(
        json.dumps([{'step': step, 'passed': True} for step in checks], indent=2),
        encoding='utf-8')
    print('PASS direct modules candidate:', ', '.join(checks))
finally:
    if name in routing.docker('ps', '-a', '--format', '{{.Names}}').splitlines():
        routing.docker('stop', name)
        routing.docker('rm', name)
    env_path.unlink(missing_ok=True)
