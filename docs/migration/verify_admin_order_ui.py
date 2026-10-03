"""Check the browser-facing Admin Order screen and module route."""
import json
import urllib.error
import urllib.request
from http_support import test_token

base = 'http://127.0.0.1:8080'
for path,marker in (('/admin.html','old_index.js'),
                    ('/assets/js/old_index.js','/api/v1/adminorderservice/adminorder')):
    with urllib.request.urlopen(base+path,timeout=20) as response:
        assert response.status == 200 and marker in response.read().decode(), path
    print('PASS '+path)

url = base+'/api/v1/adminorderservice/adminorder'
req = urllib.request.Request(url,headers={'Authorization':'Bearer '+test_token()})
with urllib.request.urlopen(req,timeout=20) as response:
    body = json.load(response)
    assert response.status == 200 and response.headers.get('X-AdminOrder-Backend') == 'module'
    assert body['status'] == 1 and len(body['data']) >= 100
print('PASS browser API serves combined list from module')

try:
    urllib.request.urlopen(url,timeout=20)
except urllib.error.HTTPError as error:
    assert error.code == 403
else:
    raise AssertionError('Admin Order API accepted anonymous request')
print('PASS browser API denies anonymous requests')
