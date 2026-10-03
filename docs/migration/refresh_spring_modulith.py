"""Refresh the active Spring Modulith host from its tested local image tag."""
import json
from pathlib import Path
import hybrid_routing as routing
from http_support import request

root=Path(__file__).resolve().parents[2]
assert 'config' not in json.loads((routing.STATE/'hybrid.json').read_text())['modules'], \
    'Historical three-module refresh cannot run after the Config cutover'
names=('station','orders','orderother')
target=routing.docker('image','inspect','train-ticket/ts-modulith:spring-modulith-1.4','--format','{{.Id}}')
previous=routing.inspect(routing.station.MODULE)['Image']
assert target!=previous,'Host is already running this image'
for name in names:assert json.loads(routing.DEFS[name]['file'].read_text())['mode']=='module'
checks=json.loads((routing.EVIDENCE/'spring-modulith-candidate.json').read_text())
assert len(checks)>=15 and all(item['passed'] for item in checks)
rollback_overlay=routing.STATE/'spring-modulith-previous-image.yml'
rollback_overlay.write_text('services:\n  modulith:\n    image: '+previous+'\n')
for name in names:routing.configure(name,'maintenance');routing.owner(name,'maintenance')
try:
    routing.docker(*routing.COMPOSE,'up','-d','modulith')
    for name in names:routing.ready(name,routing.station.MODULE)
    assert routing.inspect(routing.station.MODULE)['Image']==target
    status,model=request('http://127.0.0.1:18080','/actuator/modulith')
    assert status==200 and set(model)==set(names),(status,model)
    for name in names:routing.owner(name,'module');routing.configure(name,'module')
    state_file=routing.STATE/'spring-modulith-upgrade.json'
    state=json.loads(state_file.read_text())
    state.update(new_image=target,previous_runtime_image=previous,actuator_modules=sorted(model))
    routing.write_json(state_file,state)
    hybrid_file=routing.STATE/'hybrid.json'
    hybrid=json.loads(hybrid_file.read_text());hybrid['image']=target
    routing.write_json(hybrid_file,hybrid)
    print('Spring Modulith refreshed; actuator reports three business modules')
except Exception:
    routing.docker(*routing.COMPOSE,'-f',str(rollback_overlay),'up','-d','modulith')
    for name in names:routing.ready(name,routing.station.MODULE)
    for name in names:routing.owner(name,'module');routing.configure(name,'module')
    raise
