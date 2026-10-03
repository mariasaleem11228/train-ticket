"""Compare live Route Plan behavior against the read-only module candidate."""
import datetime
import json
from pathlib import Path
from http_support import request, wait_ready

ROOT = Path(__file__).resolve().parents[2]
PATH = '/api/v1/routeplanservice'
LIVE = 'http://127.0.0.1:14578'
CANDIDATE = 'http://127.0.0.1:18102'
checks = []

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)

wait_ready(CANDIDATE, '/actuator/health', 180)
check('welcome', request(LIVE, PATH + '/welcome') == request(CANDIDATE, PATH + '/welcome'))
modules = request(CANDIDATE, '/actuator/modulith')[1]
check('thirteen modules including Route Plan', len(modules) == 13 and
      {edge['target'] for edge in modules['routeplan']['dependencies']} ==
      {'station', 'route', 'travel', 'travel2'})
future = (datetime.datetime.now(datetime.timezone.utc) +
          datetime.timedelta(days=7)).strftime('%Y-%m-%d')
pairs = [
    ('Shang Hai', 'Nan Jing'), ('Nan Jing', 'Shang Hai'),
    ('Shang Hai', 'Su Zhou'), ('Shang Hai', 'Tai Yuan'),
    ('Nan Jing', 'Bei Jing'), ('Shang Hai', 'Bei Jing'),
]
methods = ('cheapestRoute', 'quickestRoute', 'minStopStations')
for start, end in pairs:
    body = {'formStationName': start, 'toStationName': end,
            'travelDate': future, 'num': 5}
    for method in methods:
        path = PATH + '/routePlan/' + method
        old = request(LIVE, path, 'POST', body)
        new = request(CANDIDATE, path, 'POST', body)
        # The deployed service itself returns 500 for the no-direct-trip
        # minimum-stops case; compare status without unstable error timestamps.
        equal = old == new if old[0] == 200 else old[0] == new[0]
        if not equal:
            print('legacy:', str(old)[:500], 'module:', str(new)[:500], flush=True)
        check(method + ' ' + start + ' -> ' + end, equal)
past = {'formStationName': 'Shang Hai', 'toStationName': 'Nan Jing',
        'travelDate': '2013-05-04', 'num': 5}
for method in ('cheapestRoute', 'quickestRoute'):
    path = PATH + '/routePlan/' + method
    old = request(LIVE, path, 'POST', past)
    new = request(CANDIDATE, path, 'POST', past)
    check(method + ' past-date empty result instead of legacy error',
          old[0] == 500 and new == (200, {'status': 1, 'msg': 'Success', 'data': []}))
output = ROOT / 'ts-modulith/target/evidence/route-plan-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
if not all(item['passed'] for item in checks):
    raise AssertionError('Route Plan comparison failed')
print('Route Plan comparison passed:', len(checks), 'checks')
