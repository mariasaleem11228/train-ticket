"""Compare the Go and Java News HTTP contracts before any routing change."""
import json
import urllib.error
import urllib.request
from pathlib import Path

from http_support import request, wait_ready

root = Path(__file__).resolve().parents[2]
old = 'http://127.0.0.1:12862'
new = 'http://127.0.0.1:18129'
results = []


def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    if not passed:
        raise AssertionError(label)


def get(base, path):
    with urllib.request.urlopen(base + path, timeout=20) as response:
        return response.status, response.headers.get('Content-Type'), response.read()


wait_ready(new, '/actuator/health')
status, graph = request(new, '/actuator/modulith')
check('38 Spring Modulith business modules', status == 200 and len(graph) == 38 and 'news' in graph)
check('News has no module dependencies', graph['news']['dependencies'] == [])
for label, path in (('UI route', '/news-service/news'),
                    ('other route', '/news-service/other'),
                    ('nested route', '/news-service/other/more'),
                    ('query string', '/news-service/news?source=old-ui')):
    before = get(old, path)
    after = get(new, path)
    check(label + ' matches deployed Go bytes and content type',
          before[0] == after[0] == 200 and before[2] == after[2] and
          before[1].replace(' ', '').lower() == after[1].replace(' ', '').lower())

output = root / 'ts-modulith/target/evidence/news-candidate.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('News candidate comparison passed')
