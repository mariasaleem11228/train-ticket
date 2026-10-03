"""Upgrade the shared host with Execute behind seventeen existing routes."""
import json
import hybrid_routing as routing
from http_support import request, test_token

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=17 or 'execute' in existing:
    raise RuntimeError('Expected the seventeen-module PreserveOther checkpoint')
routing.require_gate('execute-candidate.json',22)
for archive in ('execute-orders.archive','execute-order-other.archive'):
    if not (routing.STATE/'backups'/archive).exists():raise RuntimeError('Execute backup required: '+archive)
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode']!='module' for name in existing):
    raise RuntimeError('Existing routes must be in module mode')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080',
                        '/api/v1/executeservice/welcome',token=test_token())
    if status!=200 or body!='Welcome to [ Execute Service ] !':
        raise RuntimeError('Execute host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'execute'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='execute',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'execute'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Execute host prepared; existing seventeen routes remain on their modules')
