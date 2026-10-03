"""Add Notification to the shared host after isolated mail and queue checks."""
import json
import hybrid_routing as routing
from http_support import request

existing=tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing)!=27 or 'notification' in existing:
    raise RuntimeError('Expected 27-module Food checkpoint')
routing.require_gate('notification-candidate.json',18)
if not (routing.STATE/'backups/notification.archive').exists():
    raise RuntimeError('Notification Mongo backup required')
# The new host's listener stays stopped while the legacy service owns the email queue.
routing.owner('notification','legacy')
for name in existing:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:routing.ready(name,routing.station.MODULE)
    status,body=request('http://127.0.0.1:18080','/api/v1/notifyservice/welcome')
    if (status,body)!=(200,'Welcome to [ Notification Service ] !'):
        raise RuntimeError('Notification host not ready')
    status,modules=request('http://127.0.0.1:18080','/actuator/modulith')
    if status!=200 or set(modules)!=set(existing)|{'notification'}:
        raise RuntimeError('Unexpected module graph')
    state=json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='notification',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'notification'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:routing.owner(name,'module');routing.configure(name,'module')
print('Notification host ready; 27 existing routes retained')
