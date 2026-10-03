"""Compare deployed Travel2 and the module using live reads and copied write data."""
import datetime
import json
import random
from pathlib import Path
from http_support import request, test_token, wait_ready

ROOT = Path(__file__).resolve().parents[2]
PATH = '/api/v1/travel2service'
LIVE = 'http://127.0.0.1:16346'
CANDIDATE = 'http://127.0.0.1:18100'
LEGACY = 'http://127.0.0.1:26346'
MODULE = 'http://127.0.0.1:18101'
checks = []

def call(base, path, method='GET', body=None, token=None):
    return request(base, PATH + path, method, body, token)

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)

def compare(label, path, method='GET', body=None, token=None, bases=(LIVE, CANDIDATE)):
    old = call(bases[0], path, method, body, token)
    new = call(bases[1], path, method, body, token)
    if old != new:
        print('legacy:', str(old)[:600], 'module:', str(new)[:600], flush=True)
    check(label, old == new)

for base in (CANDIDATE, LEGACY, MODULE):
    wait_ready(base, '/actuator/health' if base != LEGACY else PATH + '/welcome', 300)
compare('welcome', '/welcome')
live_before = call(LIVE, '/trips')
check('five live trips retained', live_before[0] == 200 and len(live_before[1]['data']) == 5)
check('read-only candidate matches all live trips', call(CANDIDATE, '/trips') == live_before)
check('isolated copied trips match', call(LEGACY, '/trips') == call(MODULE, '/trips'))
compare('admin trip catalogue', '/admin_trip')

trips = live_before[1]['data']
for trip in trips:
    number = trip['tripId']['type'] + trip['tripId']['number']
    compare('trip ' + number, '/trips/' + number)
    compare('train type ' + number, '/train_types/' + number)
    compare('route ' + number, '/routes/' + number)
compare('trip by route batch', '/trips/routes', 'POST', [t['routeId'] for t in trips])
compare('empty route batch', '/trips/routes', 'POST', [])
compare('missing trip', '/trips/Z99999')
compare('missing route', '/routes/Z99999')
compare('missing train type', '/train_types/Z99999')

future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
search = {'startingPlace': 'Nan Jing', 'endPlace': 'Shang Hai', 'departureTime': future}
compare('journey search and fares', '/trips/left', 'POST', search)
compare('reversed journey has no matches', '/trips/left', 'POST',
        {**search, 'startingPlace': 'Shang Hai', 'endPlace': 'Nan Jing'})
compare('past journey date', '/trips/left', 'POST', {**search, 'departureTime': '2013-05-04'})
compare('missing search input', '/trips/left', 'POST', {**search, 'startingPlace': ''})
detail = {'tripId': 'Z1234', 'travelDate': future, 'from': 'Nan Jing', 'to': 'Shang Hai'}
compare('trip detail', '/trip_detail', 'POST', detail)
compare('missing trip detail', '/trip_detail', 'POST', {**detail, 'tripId': 'Z99999'})

synthetic = {**trips[0], 'tripId': 'Z' + str(random.randint(10000000, 99999999))}
synthetic['startingTime'] = trips[0]['startingTime']
synthetic['endTime'] = trips[0]['endTime']
path = '/trips/' + synthetic['tripId']
check('candidate rejects writes', call(CANDIDATE, '/trips', 'POST', synthetic)[0] == 503)
check('unauthenticated update follows deployed access rule',
      call(LEGACY, '/trips', 'PUT', synthetic) == call(MODULE, '/trips', 'PUT', synthetic))
admin = test_token()
try:
    compare('create', '/trips', 'POST', synthetic, bases=(LEGACY, MODULE))
    compare('created trip lookup', path, bases=(LEGACY, MODULE))
    compare('duplicate create', '/trips', 'POST', synthetic, bases=(LEGACY, MODULE))
    changed = {**synthetic, 'stationsId': 'wuxi'}
    compare('update', '/trips', 'PUT', changed, admin, bases=(LEGACY, MODULE))
    compare('updated trip lookup', path, bases=(LEGACY, MODULE))
    compare('delete', path, 'DELETE', token=admin, bases=(LEGACY, MODULE))
    compare('deleted trip lookup', path, bases=(LEGACY, MODULE))
finally:
    for base in (LEGACY, MODULE):
        if call(base, path)[1].get('status') == 1:
            call(base, path, 'DELETE', token=admin)
check('live trips unchanged', call(LIVE, '/trips') == live_before)
modules = request(CANDIDATE, '/actuator/modulith')[1]
check('Travel2 only uses Train, Route, Orders and Seat',
      set(modules['travel2']['allowedDependencies']) == {'train', 'route', 'orders', 'seat'} and
      {dependency['target'] for dependency in modules['travel2']['dependencies']} ==
      {'train', 'route', 'orders', 'seat'})
output = ROOT / 'ts-modulith/target/evidence/travel2-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
if not all(item['passed'] for item in checks):
    raise AssertionError('Travel2 comparison failed')
print('Travel2 comparison passed:', len(checks), 'checks')
