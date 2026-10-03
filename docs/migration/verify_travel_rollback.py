"""Rehearse Travel write handover to legacy and back on a disposable trip."""
import json
import secrets
import urllib.request

import hybrid_routing as routing
from http_support import request, test_token

PATH = '/api/v1/travelservice'
PORT = 'http://127.0.0.1:12346'
MODULE = 'http://127.0.0.1:18080'
ADMIN = test_token()


def call(base, suffix, method='GET', body=None, token=None):
    return request(base, PATH + suffix, method, body, token)


def check(label, condition):
    print(('PASS ' if condition else 'FAIL ') + label, flush=True)
    if not condition:
        raise AssertionError(label)


def backend():
    with urllib.request.urlopen(PORT + PATH + '/welcome', timeout=20) as response:
        return response.headers.get('X-Travel-Backend')


state = json.loads(routing.DEFS['travel']['file'].read_text())
if state['mode'] != 'module':
    raise RuntimeError('Travel must start on its module route')

baseline = call(PORT, '/trips')
check('module serves original five trips', baseline[0] == 200 and
      len(baseline[1]['data']) == 5 and backend() == 'module')
trip = {**baseline[1]['data'][0], 'tripId': 'G' + str(secrets.randbelow(90000000) + 10000000)}
trip_path = '/trips/' + trip['tripId']
created = False
handover_complete = False
try:
    status, response = call(PORT, '/trips', 'POST', trip)
    created = status == 201 and response.get('status') == 1
    check('module creates disposable trip', status == 201 and response.get('status') == 1)
    check('module reads disposable trip', call(PORT, trip_path)[1].get('status') == 1)

    routing.switch('travel', 'legacy')
    check('legacy serves original service identity', backend() == 'legacy')
    check('legacy reads module-created trip', call(PORT, trip_path)[1].get('status') == 1)

    changed = {**trip, 'stationsId': 'wuxi'}
    status, response = call(PORT, '/trips', 'PUT', changed, ADMIN)
    check('legacy updates disposable trip', status == 200 and response.get('status') == 1)
    legacy_read = call(PORT, trip_path)
    check('legacy reads updated station IDs', legacy_read[1]['data']['stationsId'] == 'wuxi')
    check('module rejects writes during legacy ownership',
          call(MODULE, '/trips', 'PUT', trip, ADMIN)[0] == 503)
    handover_complete = True
finally:
    mode = json.loads(routing.DEFS['travel']['file'].read_text())['mode']
    if mode != 'module':
        routing.switch('travel', 'module')
    if created:
        try:
            if handover_complete:
                module_read = call(PORT, trip_path)
                check('module reads legacy update after return',
                      backend() == 'module' and module_read[1]['data']['stationsId'] == 'wuxi')
        finally:
            status, response = call(PORT, trip_path, 'DELETE', token=ADMIN)
            check('disposable trip removed', status == 200 and response.get('status') == 1)

check('original five trips unchanged', call(PORT, '/trips') == baseline)
print('Travel rollback rehearsal passed', flush=True)
