"""Read new-runtime orders on the previous image, then return to Spring Modulith."""
import json
import subprocess
from pathlib import Path
import hybrid_routing as routing

root=Path(__file__).resolve().parents[2]
names=('station','orders','orderother')
state=json.loads((routing.STATE/'spring-modulith-upgrade.json').read_text())
assert state['status']=='complete'
assert routing.inspect(routing.station.MODULE)['Image']==state['new_image']
for name in names:
    assert json.loads(routing.DEFS[name]['file'].read_text())['mode']=='module'

def activate(compose,image):
    for name in names:
        routing.configure(name,'maintenance')
        routing.owner(name,'maintenance')
    routing.docker(*compose,'up','-d','modulith')
    for name in names:routing.ready(name,routing.station.MODULE)
    assert routing.inspect(routing.station.MODULE)['Image']==image
    for name in names:
        routing.owner(name,'module')
        routing.configure(name,'module')

old_verified=False
try:
    activate(routing.BASE_COMPOSE,state['old_image'])
    subprocess.run(['python',str(root/'docs/migration/verify_checkpoint.py'),'--legacy-framework'],check=True)
    old_verified=True
finally:
    activate(routing.COMPOSE,state['new_image'])
subprocess.run(['python',str(root/'docs/migration/verify_checkpoint.py')],check=True)
(routing.EVIDENCE/'spring-modulith-rollback.json').write_text(json.dumps({
    'old_image_read_new_orders':old_verified,'new_image_restored':True,
    'old_image':state['old_image'],'new_image':state['new_image']},indent=2))
print('Framework rollback and return passed')
