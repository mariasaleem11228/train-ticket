"""Check Ticket Office browser routes and module identity after cutover."""
import json
import urllib.request

from http_support import request

status, graph = request('http://127.0.0.1:18080', '/actuator/modulith')
if status != 200 or 'ticketoffice' not in graph or graph['ticketoffice']['dependencies']:
    raise AssertionError('Unexpected Ticket Office module graph')
for path in ('/office/getRegionList', '/office/getAll'):
    with urllib.request.urlopen('http://127.0.0.1:16108' + path, timeout=20) as direct:
        direct_body = json.load(direct)
        if direct.status != 200 or direct.headers.get('X-TicketOffice-Backend') != 'module':
            raise AssertionError('Direct Ticket Office route is not serving from module')
    with urllib.request.urlopen('http://127.0.0.1:8080' + path, timeout=20) as public:
        if public.status != 200 or public.headers.get('X-TicketOffice-Backend') != 'module' or json.load(public) != direct_body:
            raise AssertionError('Public Ticket Office route differs from module')
print('PASS Ticket Office module graph, direct route, and browser routes')
