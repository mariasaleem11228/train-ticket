"""Check that the public and direct News routes serve the Spring Modulith module."""
import urllib.request

from http_support import request

status, graph = request('http://127.0.0.1:18080', '/actuator/modulith')
if status != 200 or 'news' not in graph or graph['news']['dependencies']:
    raise AssertionError('Unexpected News module graph')
for path in ('/news-service/news', '/news-service/other'):
    with urllib.request.urlopen('http://127.0.0.1:12862' + path, timeout=20) as direct:
        direct_body = direct.read()
        if direct.status != 200 or direct.headers.get('X-News-Backend') != 'module':
            raise AssertionError('Direct News route is not serving from module')
    if path == '/news-service/news':
        with urllib.request.urlopen('http://127.0.0.1:8080' + path, timeout=20) as public:
            if public.status != 200 or public.headers.get('X-News-Backend') != 'module' or public.read() != direct_body:
                raise AssertionError('Public News route differs from module')
print('PASS News module graph, direct route, and public UI route')
