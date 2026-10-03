"""Compare deployed Basic with a read-only candidate over the live catalogues."""
import json
from pathlib import Path
from urllib.parse import quote
from http_support import request, wait_ready

ROOT = Path(__file__).resolve().parents[2]
LEGACY = 'http://127.0.0.1:15680'
MODULE = 'http://127.0.0.1:18097'
PATH = '/api/v1/basicservice'
checks = []

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

def compare(label, path, method='GET', body=None):
    old = request(LEGACY, path, method, body)
    new = request(MODULE, path, method, body)
    # Old/new Spring Boot versions format exception JSON differently.
    passed = old == new if old[0] < 500 else old[0] == new[0]
    if not passed:
        print('legacy:', old, 'module:', new, flush=True)
    check(label, passed)

wait_ready(MODULE, '/actuator/health', 300)
compare('welcome', PATH + '/welcome')
station_result = request('http://127.0.0.1:12345', '/api/v1/stationservice/stations')
check('live station catalogue available', station_result[0] == 200 and station_result[1]['status'] == 1)
names = {s['id']: s['name'] for s in station_result[1]['data']}
for name in list(names.values())[:5] + ['migration-no-such-station']:
    compare('station ID for ' + name, PATH + '/basic/' + quote(name))

price_result = request('http://127.0.0.1:16579', '/api/v1/priceservice/prices')
check('live price catalogue available', price_result[0] == 200 and price_result[1]['status'] == 1)
cases = []
for price in price_result[1]['data']:
    route = request('http://127.0.0.1:11178', '/api/v1/routeservice/routes/' + price['routeId'])
    if route[0] != 200 or route[1]['status'] != 1:
        continue
    ids = route[1]['data']['stations']
    if len(ids) < 2 or ids[0] not in names or ids[1] not in names:
        continue
    body = {'trip': {'trainTypeId': price['trainType'], 'routeId': price['routeId']},
            'startingPlace': names[ids[0]], 'endPlace': names[ids[1]]}
    cases.append(body)
    compare('travel price for ' + price['routeId'], PATH + '/basic/travel', 'POST', body)
check('real travel cases tested', len(cases) >= 5)

base = cases[0]
compare('unknown starting station', PATH + '/basic/travel', 'POST',
        {**base, 'startingPlace': 'migration-no-such-station'})
compare('unknown route', PATH + '/basic/travel', 'POST',
        {**base, 'trip': {**base['trip'], 'routeId': 'migration-no-such-route'}})
compare('reversed stations', PATH + '/basic/travel', 'POST',
        {**base, 'startingPlace': base['endPlace'], 'endPlace': base['startingPlace']})
compare('same station', PATH + '/basic/travel', 'POST',
        {**base, 'endPlace': base['startingPlace']})
compare('unknown train remains an error', PATH + '/basic/travel', 'POST',
        {**base, 'trip': {**base['trip'], 'trainTypeId': 'migration-no-such-train'}})
modules = request(MODULE, '/actuator/modulith')[1]
check('Basic only depends on four catalogues',
      set(modules['basic']['allowedDependencies']) == {'station', 'train', 'route', 'price'} and
      {edge['target'] for edge in modules['basic']['dependencies']} ==
      {'station', 'train', 'route', 'price'})
output = ROOT / 'ts-modulith/target/evidence/basic-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
print('Basic comparison passed:', len(checks), 'checks')
