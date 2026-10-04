"""HTTP helpers for local benchmark migration tests (stdlib only)."""
import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

def test_token(role='ROLE_ADMIN', account_id=None):
    # Existing Train Ticket benchmark key. Test credentials, never a production identity.
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).rstrip(b'=')
    claims={'sub': 'station-migration-test', 'roles': [role], 'exp': int(time.time()) + 3600}
    if account_id is not None:claims['id']=account_id
    value = encode({'alg': 'HS256', 'typ': 'JWT'}) + b'.' + encode(claims)
    return (value + b'.' + base64.urlsafe_b64encode(hmac.new(b'secret', value, hashlib.sha256).digest()).rstrip(b'=')).decode()

def request(base, path, method='GET', body=None, token=None):
    headers = {}
    if token is not None:
        headers['Authorization'] = 'Bearer ' + token
    payload = None
    if body is not None:
        headers['Content-Type'] = 'application/json'
        payload = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(base + path, data=payload, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as ex:
        response = ex
    with response:
        data = response.read().decode('utf-8')
        try:
            data = json.loads(data)
        except ValueError:
            pass
        return response.status, data

def wait_ready(base, path='/api/v1/stationservice/stations', seconds=180):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            status, data = request(base, path)
            if status == 200 and (not isinstance(data, dict) or data.get('status') in (1, 'UP')):
                return
        except (OSError, urllib.error.URLError):
            pass
        print('Waiting for', base, flush=True)
        time.sleep(3)
    raise RuntimeError('Readiness deadline exceeded: ' + base)
