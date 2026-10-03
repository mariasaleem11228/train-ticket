"""Upgrade the shared host after isolated Voucher contract checks."""
import json
import hybrid_routing as routing
from http_support import request

existing = tuple(json.loads((routing.STATE/'hybrid.json').read_text())['modules'])
if len(existing) != 36 or 'voucher' in existing:
    raise RuntimeError('Expected 36-module Admin User checkpoint')
routing.require_gate('voucher-candidate.json',10)
if not (routing.STATE/'backups/voucher.sql').exists():
    raise RuntimeError('Voucher MySQL backup required')
routing.owner('voucher','legacy')
for name in existing:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in existing:
        routing.ready(name,routing.station.MODULE)
    status,_ = request('http://127.0.0.1:18080','/getVoucher')
    if status != 405: raise RuntimeError('Voucher host route not ready')
    status,modules = request('http://127.0.0.1:18080','/actuator/modulith')
    if status != 200 or set(modules) != set(existing)|{'voucher'}:
        raise RuntimeError('Unexpected module graph')
    state = json.loads((routing.STATE/'hybrid.json').read_text())
    state.update(stage='voucher',image=routing.inspect(routing.station.MODULE)['Image'],
                 modules=[*existing,'voucher'])
    routing.write_json(routing.STATE/'hybrid.json',state)
except Exception:
    routing.docker(*routing.COMPOSE[:-2],'up','-d','modulith')
    raise
finally:
    for name in existing:
        routing.owner(name,'module')
        routing.configure(name,'module')
print('Voucher host ready; 36 existing routes retained')
