"""Rehearse Avatar legacy fallback and return to the module using a fixed face image."""
import base64
import hashlib
import json
import urllib.request

import hybrid_routing as routing

face = base64.b64encode((routing.ROOT / 'ts-avatar-service/images/test.png').read_bytes()).decode()
expected = 'b2b3923b58e078a56696d27968414baf65b3b7c81c90be32c609a150c9010d7a'


def probe(mode):
    req = urllib.request.Request('http://127.0.0.1:8080/api/v1/avatar',
                                 json.dumps({'img': face}).encode(),
                                 {'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as response:
        return (response.status == 200 and response.headers.get('X-Avatar-Backend') == mode
                and hashlib.sha256(response.read()).hexdigest() == expected)


assert probe('module'), 'Avatar module baseline failed'
routing.switch('avatar', 'legacy')
try:
    assert probe('legacy'), 'Avatar legacy fallback failed'
finally:
    routing.switch('avatar', 'module')
assert probe('module'), 'Avatar module return failed'
print('PASS Avatar module-to-legacy-to-module face crop and backend header')
