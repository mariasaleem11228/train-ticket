"""Rehearse News module -> deployed Go -> module routing without changing data."""
import json
import urllib.request

import hybrid_routing as routing


def probe(mode):
    with urllib.request.urlopen('http://127.0.0.1:12862/news-service/news', timeout=20) as response:
        if response.status != 200 or response.headers.get('X-News-Backend') != mode:
            raise AssertionError(f'News was not served by {mode}')
        body = response.read()
        if b'News Service Complete' not in body:
            raise AssertionError('Unexpected News body')
        print('PASS News', mode, flush=True)


if json.loads(routing.DEFS['news']['file'].read_text())['mode'] != 'module':
    raise RuntimeError('News must start in module mode')
probe('module')
try:
    routing.switch('news', 'legacy')
    probe('legacy')
finally:
    if json.loads(routing.DEFS['news']['file'].read_text())['mode'] != 'module':
        routing.switch('news', 'module')
probe('module')
print('News rollback rehearsal passed')
