"""Upgrade shared host with Rebook behind twenty-one existing routes."""
import json
import hybrid_routing as routing
from http_support import request,test_token

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=21 or 'rebook' in existing:
    raise RuntimeError('Expected the twenty-one-module Cancel checkpoint')
routing.require_gate('rebook-candidate.json',74)
for archive in ('rebook-orders.archive','rebook-order-other.archive','rebook-wallet-payment.archive'):
    if not (routing.STATE/'backups'/archive).exists():
        raise RuntimeError('Rebook dependency backup required: '+archive)
if any(json.loads(routing.DEFS[name]['file'].read_text())['mode']!='module' for name in existing):
    raise RuntimeError('Existing routes must be in module mode')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080',
                        '/api/v1/rebookservice/welcome',token=test_token())
    if status!=200 or body!='Welcome to [ Rebook Service ] !':
        raise RuntimeError('Rebook host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'rebook'}:
        raise RuntimeError('Unexpected Spring Modulith module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='rebook',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'rebook'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Rebook host prepared; existing twenty-one routes remain on their modules')
