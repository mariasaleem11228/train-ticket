"""Run Admin Travel beside legacy using isolated Travel and Travel2 copies."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
names = subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for service in ('travel','travel2'):
    matches = [name for name in names if name.endswith('train-ticket-ts-'+service+'-mongo-1')]
    if len(matches) != 1:
        raise RuntimeError('Expected one '+service+' Mongo container')
    mongo = matches[0]
    archive = '/tmp/admin-travel-'+service+'.archive'
    subprocess.run(['docker','exec',mongo,'mongodump','--db=ts','--archive='+archive],check=True)
    subprocess.run(['docker','exec',mongo,'mongorestore','--archive='+archive,
                    '--nsFrom=ts.*','--nsTo=ts-admin-travel-candidate.*','--drop'],check=True)

host = json.loads(subprocess.check_output(
    ['docker','inspect','station-migration-modulith-1'],text=True))[0]
env = dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
for service in ('TRAVEL','TRAVEL2'):
    env[service+'_WRITES_ENABLED'] = 'true'
    env[service+'_MONGO_URI'] = ('mongodb://ts-'+service.lower()+'-mongo:27017/'
                                 'ts-admin-travel-candidate')
env.update(ADMIN_TRAVEL_ENABLED='true',MODULITH_OWNERSHIP_FILE='')
file = root/'ts-modulith/target/admin-travel-candidate.env'
file.write_text(''.join(k+'='+v+'\n' for k,v in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','admin-travel-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18125:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:admin-travel-candidate'],check=True)
print('Admin Travel candidate launched against isolated Travel snapshots')
