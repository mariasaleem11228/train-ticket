"""Rehearse Route Plan's independent read-only rollback and return."""
import datetime
import json
import urllib.request
import hybrid_routing as routing
from http_support import request

PATH = '/api/v1/routeplanservice'
PORT = 'http://127.0.0.1:14578'
MODULE = 'http://127.0.0.1:18080'
body = {'formStationName': 'Shang Hai', 'toStationName': 'Nan Jing',
        'num': 5, 'travelDate': (datetime.datetime.now(datetime.timezone.utc) +
        datetime.timedelta(days=7)).strftime('%Y-%m-%d')}

def backend():
    with urllib.request.urlopen(PORT + PATH + '/welcome', timeout=20) as response:
        return response.headers.get('X-RoutePlan-Backend')

def check(label, passed):
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

state = json.loads(routing.DEFS['routeplan']['file'].read_text())
if state['mode'] != 'module':
    raise RuntimeError('Route Plan must start on its module route')
path = PATH + '/routePlan/cheapestRoute'
before = request(PORT, path, 'POST', body)
check('module serves journey ranking', before == request(MODULE, path, 'POST', body)
      and backend() == 'module')
try:
    routing.switch('routeplan', 'legacy')
    check('legacy serves original identity', backend() == 'legacy')
    check('ranking survives rollback', request(PORT, path, 'POST', body) == before)
finally:
    if json.loads(routing.DEFS['routeplan']['file'].read_text())['mode'] != 'module':
        routing.switch('routeplan', 'module')
check('module serves original identity again', backend() == 'module')
check('ranking survives return', request(PORT, path, 'POST', body) == before)
print('Route Plan rollback rehearsal passed', flush=True)
