"""Read-only comparison of the deployed Seat service and five-module candidate."""
import datetime
import json
from pathlib import Path
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
LEGACY = 'http://127.0.0.1:28898'
CANDIDATE = 'http://127.0.0.1:18088'
PATH = '/api/v1/seatservice'
checks = []


def check(label, condition):
    checks.append({'step': label, 'passed': bool(condition)})
    print(('PASS' if condition else 'FAIL') + ' ' + label, flush=True)
    if not condition:
        raise AssertionError(label)


def call(base, endpoint, body):
    return request(base, PATH + endpoint, 'POST', body, test_token())


status, model = request(CANDIDATE, '/actuator/modulith')
check('candidate declares five modules', status == 200 and
      set(model) == {'station', 'orders', 'orderother', 'config', 'seat'})
check('Seat depends on local Orders, OrderOther and Config',
      {edge['target'] for edge in model['seat']['dependencies']} ==
      {'orders', 'orderother', 'config'})
check('welcome matches', request(LEGACY, PATH + '/welcome') ==
      request(CANDIDATE, PATH + '/welcome'))

date = (datetime.datetime.now(datetime.timezone.utc) +
        datetime.timedelta(days=7)).strftime('%Y-%m-%d')
journeys = []
for branch in ('travelservice', 'travel2service'):
    status, response = request('http://127.0.0.1:8080',
                               '/api/v1/' + branch + '/trips/left', 'POST',
                               {'startingPlace': 'Nan Jing', 'endPlace': 'Shang Hai',
                                'departureTime': date}, test_token())
    check(branch + ' search supplies a trip', status == 200 and bool(response.get('data')))
    trip = response['data'][0]['tripId']
    number = str(trip['type']) + str(trip['number']) if isinstance(trip, dict) else trip
    journeys.append(number)

for number in journeys:
    for seat_type in (2, 3):
        for start in ('nanjing', 'suzhou' if number.startswith(('G', 'D')) else 'shijiazhuang'):
            body = {'travelDate': date, 'trainNumber': number,
                    'startStation': start, 'destStation': 'shanghai',
                    'seatType': seat_type}
            old = call(LEGACY, '/seats/left_tickets', body)
            new = call(CANDIDATE, '/seats/left_tickets', body)
            check(number + ' class ' + str(seat_type) + ' from ' + start + ' availability matches',
                  old == new and old[0] == 200 and old[1]['status'] == 1)
        body = {'travelDate': date, 'trainNumber': number,
                'startStation': 'nanjing', 'destStation': 'shanghai',
                'seatType': seat_type}
        old = call(LEGACY, '/seats', body)
        new = call(CANDIDATE, '/seats', body)
        def valid(result):
            http, response = result
            ticket = response.get('data') or {}
            return (http == 200 and response.get('status') == 1 and
                    response.get('msg') in ('Use a new seat number!',
                                            'Use the previous distributed seat number!') and
                    isinstance(ticket.get('seatNo'), int) and ticket['seatNo'] > 0 and
                    ticket.get('startStation') == body['startStation'] and
                    ticket.get('destStation') == body['destStation'])
        check(number + ' class ' + str(seat_type) + ' assignment contract matches',
              valid(old) and valid(new) and old[1]['msg'] == new[1]['msg'])

output = ROOT / 'ts-modulith/target/evidence/seat-candidate.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Seat candidate comparison passed:', len(checks), 'checks')
