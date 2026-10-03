"""Upgrade the existing three-module host to Spring Modulith with rollback."""
import json
import sys
from pathlib import Path
import hybrid_routing as routing

root=Path(__file__).resolve().parents[2]
state_file=root/'deployment/migration/.state/spring-modulith-upgrade.json'
hybrid_file=routing.STATE/'hybrid.json'
image='train-ticket/ts-modulith:spring-modulith-1.4'
modules=('station','orders','orderother')

checks=json.loads((routing.EVIDENCE/'spring-modulith-candidate.json').read_text())
assert len(checks)>=15 and all(item['passed'] for item in checks)
assert not state_file.exists() or json.loads(state_file.read_text()).get('status')=='rolled-back'
for name in modules:
    assert json.loads(routing.DEFS[name]['file'].read_text())['mode']=='module',name
old_image=routing.inspect(routing.station.MODULE)['Image']
target_image=routing.docker('image','inspect',image,'--format','{{.Id}}')
assert old_image!=target_image
routing.write_json(state_file,{'status':'in-progress','old_image':old_image,'new_image':target_image})
for name in modules:
    routing.configure(name,'maintenance')
    routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in modules:routing.ready(name,routing.station.MODULE)
    assert routing.inspect(routing.station.MODULE)['Image']==target_image
    for name in modules:
        routing.owner(name,'module')
        routing.configure(name,'module')
    hybrid=json.loads(hybrid_file.read_text())
    hybrid.update(framework='Spring Modulith 1.4.13',image=target_image)
    routing.write_json(hybrid_file,hybrid)
    routing.write_json(state_file,{'status':'complete','old_image':old_image,'new_image':target_image})
    print('Shared host upgraded to Spring Modulith; all three modules routed to it')
except Exception:
    routing.docker(*routing.BASE_COMPOSE,'up','-d','modulith')
    for name in modules:
        routing.ready(name,routing.station.MODULE)
        routing.owner(name,'module')
        routing.configure(name,'module')
    routing.write_json(state_file,{'status':'rolled-back','old_image':old_image,'new_image':target_image})
    raise
