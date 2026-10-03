"""Compare deployed Travel Plan and the read-only module candidate."""
import datetime
import json
from pathlib import Path
from http_support import request, wait_ready

ROOT = Path(__file__).resolve().parents[2]
PATH = '/api/v1/travelplanservice'
LIVE = 'http://127.0.0.1:14322'
CANDIDATE = 'http://127.0.0.1:18103'
checks = []

def check(label, passed):
    checks.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)

def compare(label, suffix, body=None):
    old = request(LIVE, PATH + suffix, 'POST' if body is not None else 'GET', body)
    new = request(CANDIDATE, PATH + suffix, 'POST' if body is not None else 'GET', body)
    # Legacy error bodies include nondeterministic timestamps and exception text.
    equal = old == new if old[0] == 200 else old[0] == new[0]
    if not equal:
        print('legacy:', str(old)[:500], 'module:', str(new)[:500], flush=True)
    check(label, equal)

wait_ready(CANDIDATE, '/actuator/health', 180)
compare('welcome', '/welcome')
modules = request(CANDIDATE, '/actuator/modulith')[1]
check('fourteen modules with published Travel Plan dependencies',
      len(modules) == 14 and
      {edge['target'] for edge in modules['travelplan']['dependencies']} ==
      {'station','seat','travel','travel2','routeplan'})
future = (datetime.datetime.now(datetime.timezone.utc) +
          datetime.timedelta(days=7)).strftime('%Y-%m-%d')
pairs = [
    ('Shang Hai', 'Nan Jing'), ('Nan Jing', 'Shang Hai'),
    ('Shang Hai', 'Su Zhou'), ('Shang Hai', 'Tai Yuan'),
    ('Nan Jing', 'Bei Jing'), ('Shang Hai', 'Bei Jing'),
]
for start, end in pairs:
    body = {'startingPlace': start, 'endPlace': end, 'departureTime': future}
    for method in ('cheapest','quickest','minStation'):
        compare(method + ' ' + start + ' -> ' + end, '/travelPlan/' + method, body)
past = {'startingPlace': 'Shang Hai', 'endPlace': 'Nan Jing',
        'departureTime': '2013-05-04'}
for method in ('cheapest','quickest','minStation'):
    compare(method + ' past date', '/travelPlan/' + method, past)
for start, via, end in [
        ('Nan Jing','Su Zhou','Shang Hai'),
        ('Shang Hai','Nan Jing','Bei Jing'),
        ('Bei Jing','Su Zhou','Tai Yuan')]:
    body = {'fromStationName': start, 'viaStationName': via,
            'toStationName': end, 'travelDate': future, 'trainType': 'All'}
    compare('transfer ' + start + ' via ' + via + ' -> ' + end,
            '/travelPlan/transferResult', body)
output = ROOT / 'ts-modulith/target/evidence/travel-plan-comparison.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(checks, indent=2), encoding='utf-8')
if not all(item['passed'] for item in checks):
    raise AssertionError('Travel Plan comparison failed')
print('Travel Plan comparison passed:', len(checks), 'checks')
