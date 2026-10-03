"""Rehearse Basic's independent read-only rollback and return to the module."""
import json
import urllib.request
import hybrid_routing as routing
from http_support import request

PATH = '/api/v1/basicservice'
PORT = 'http://127.0.0.1:15680'
MODULE = 'http://127.0.0.1:18080'

def backend():
    with urllib.request.urlopen(PORT + PATH + '/welcome', timeout=20) as response:
        return response.headers.get('X-Basic-Backend'), response.read().decode()

def check(label, condition):
    print(('PASS ' if condition else 'FAIL ') + label, flush=True)
    if not condition:
        raise AssertionError(label)

state = json.loads(routing.DEFS['basic']['file'].read_text())
if state['mode'] != 'module':
    raise RuntimeError('Basic must start on the module route')
before = request(PORT, PATH + '/basic/Shang%20Hai')
check('module serves station lookup', before == request(MODULE, PATH + '/basic/Shang%20Hai'))
try:
    routing.switch('basic', 'legacy')
    check('legacy Basic serves on original identity', backend() ==
          ('legacy', 'Welcome to [ Basic Service ] !'))
    check('station lookup survives rollback', request(PORT, PATH + '/basic/Shang%20Hai') == before)
finally:
    routing.switch('basic', 'module')
check('Basic returns to module route', backend() ==
      ('module', 'Welcome to [ Basic Service ] !'))
check('station lookup survives return', request(PORT, PATH + '/basic/Shang%20Hai') == before)
print('Basic rollback rehearsal passed')
