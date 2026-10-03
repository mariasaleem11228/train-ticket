"""Compare safe failures and exercise a booking in an isolated Orders database."""
import datetime
import json
import uuid
from pathlib import Path
from http_support import request

root = Path(__file__).resolve().parents[2]
fixture = json.loads((root/'deployment/migration/.state/e2e/fixture.json').read_text())
legacy = 'http://127.0.0.1:14568'
module = 'http://127.0.0.1:18106'
path = '/api/v1/preserveservice/preserve'
date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
results = []

def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

def call(host, body):
    return request(host, path, 'POST', body, fixture['token'])

check('welcome matches deployed service',
      request(legacy, '/api/v1/preserveservice/welcome', token=fixture['token']) ==
      request(module, '/api/v1/preserveservice/welcome', token=fixture['token']))
check('candidate has sixteen business modules',
      len(request(module, '/actuator/modulith')[1]) == 16)
search = request('http://127.0.0.1:8080', '/api/v1/travelservice/trips/left', 'POST',
                 {'startingPlace': 'Nan Jing', 'endPlace': 'Shang Hai', 'departureTime': date},
                 fixture['token'])
check('live search returns a trip', search[0] == 200 and search[1]['status'] == 1
      and bool(search[1]['data']))
trip = search[1]['data'][0]['tripId']
if isinstance(trip, dict):
    trip = str(trip['type']) + str(trip['number'])
body = {'accountId': fixture['userId'], 'contactsId': str(uuid.uuid4()),
        'tripId': trip, 'seatType': 3, 'date': date,
        'from': 'Nan Jing', 'to': 'Shang Hai', 'assurance': 0, 'foodType': 0}
check('missing contact matches deployed response', call(legacy, body) == call(module, body))
body['contactsId'] = fixture['contactId']
status, response = call(module, body)
check('isolated candidate books via local modules', status == 200 and
      response == {'status': 1, 'msg': 'Success.', 'data': 'Success'})
first_class = dict(body, seatType=2)
status, response = call(module, first_class)
check('isolated candidate books first class', status == 200 and
      response == {'status': 1, 'msg': 'Success.', 'data': 'Success'})
query = {'loginId': fixture['userId'], 'enableStateQuery': False,
         'enableTravelDateQuery': False, 'enableBoughtDateQuery': False}
status, orders = request(module, '/api/v1/orderservice/order/query', 'POST', query, fixture['token'])
check('both bookings persisted in isolated Orders database', status == 200 and
      orders['status'] == 1 and
      {order['seatClass'] for order in orders['data'] if order['trainNumber'] == trip
       and order['status'] == 0} >= {2, 3})
output = root/'ts-modulith/target/evidence/preserve-candidate.json'
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Preserve candidate comparison passed')
