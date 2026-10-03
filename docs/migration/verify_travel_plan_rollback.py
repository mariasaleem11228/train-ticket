"""Rehearse Travel Plan's independent read-only rollback and return."""
import datetime
import json
import urllib.request
import hybrid_routing as routing
from http_support import request

PATH = '/api/v1/travelplanservice'
PORT = 'http://127.0.0.1:14322'
MODULE = 'http://127.0.0.1:18080'
body = {'startingPlace': 'Shang Hai', 'endPlace': 'Nan Jing',
        'departureTime': (datetime.datetime.now(datetime.timezone.utc) +
        datetime.timedelta(days=7)).strftime('%Y-%m-%d')}

def backend():
    with urllib.request.urlopen(PORT + PATH + '/welcome', timeout=20) as response:
        return response.headers.get('X-TravelPlan-Backend')

def check(label, passed):
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)

state = json.loads(routing.DEFS['travelplan']['file'].read_text())
if state['mode'] != 'module':
    raise RuntimeError('Travel Plan must start on its module route')
path = PATH + '/travelPlan/cheapest'
before = request(PORT, path, 'POST', body)
check('module serves advanced search', before == request(MODULE, path, 'POST', body)
      and backend() == 'module')
try:
    routing.switch('travelplan', 'legacy')
    check('legacy serves original identity', backend() == 'legacy')
    check('advanced search survives rollback', request(PORT, path, 'POST', body) == before)
finally:
    if json.loads(routing.DEFS['travelplan']['file'].read_text())['mode'] != 'module':
        routing.switch('travelplan', 'module')
check('module serves original identity again', backend() == 'module')
check('advanced search survives return', request(PORT, path, 'POST', body) == before)
print('Travel Plan rollback rehearsal passed', flush=True)
