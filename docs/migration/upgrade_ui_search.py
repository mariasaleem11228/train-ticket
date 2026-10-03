"""Deploy the browser search contract fix behind the existing 17 module routes."""
import datetime
import json
import hybrid_routing as routing
from http_support import request, test_token

names = tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(names) != 17 or any(json.loads(routing.DEFS[name]['file'].read_text())['mode'] != 'module'
                           for name in names):
    raise RuntimeError('Expected all seventeen routes in module mode')

old_image = routing.inspect(routing.station.MODULE)['Image']
for name in names:
    routing.configure(name, 'maintenance')
    routing.owner(name, 'maintenance')
try:
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    routing.ready('travel', routing.station.MODULE)
    state = json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(image=routing.inspect(routing.station.MODULE)['Image'], stage='preserveother-ui-compat')
    routing.write_json(routing.STATE/'hybrid.json', state)
except Exception:
    # The previous immutable image remains available for this local rollback.
    routing.docker('tag', old_image, 'train-ticket/ts-modulith:preserve-other-ui-fix')
    routing.docker(*routing.COMPOSE, 'up', '-d', 'modulith')
    routing.ready('travel', routing.station.MODULE)
    raise
finally:
    for name in names:
        routing.owner(name, 'module')
        routing.configure(name, 'module')
date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
body = {'startPlace': 'Nan Jing', 'endPlace': 'Shang Hai', 'departureTime': date + ' 00:00:00'}
for service in ('travelservice', 'travel2service'):
    status, result = request('http://127.0.0.1:8080',
                             f'/api/v1/{service}/trips/left', 'POST', body, test_token())
    if status != 200 or result.get('status') != 1 or not result.get('data'):
        raise RuntimeError(service + ' did not return journeys for the browser request')
print('Browser search contract fixed; all seventeen routes restored to module mode')
