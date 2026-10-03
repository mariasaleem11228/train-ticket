"""Run Admin Route beside legacy against an isolated Route database copy."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
names = subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches = [name for name in names if name.endswith('train-ticket-ts-route-mongo-1')]
if len(matches) != 1:
    raise RuntimeError('Expected one Route Mongo container')
mongo = matches[0]
archive = '/tmp/admin-route-candidate.archive'
subprocess.run(['docker','exec',mongo,'mongodump','--db=ts','--archive='+archive],check=True)
subprocess.run(['docker','exec',mongo,'mongorestore','--archive='+archive,
                '--nsFrom=ts.*','--nsTo=ts-admin-route-candidate.*','--drop'],check=True)

host = json.loads(subprocess.check_output(
    ['docker','inspect','station-migration-modulith-1'],text=True))[0]
env = dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(ADMIN_ROUTE_ENABLED='true',ROUTE_WRITES_ENABLED='true',
           ROUTE_MONGO_URI='mongodb://ts-route-mongo:27017/ts-admin-route-candidate',
           MODULITH_OWNERSHIP_FILE='')
file = root/'ts-modulith/target/admin-route-candidate.env'
file.write_text(''.join(k+'='+v+'\n' for k,v in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','admin-route-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18124:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:admin-route-candidate'],check=True)
print('Admin Route candidate launched against isolated Route snapshot')
