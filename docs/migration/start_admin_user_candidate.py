"""Run Admin User beside legacy using isolated User and Auth copies."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
names = subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for service,source in (('user','ts-user-mongo'),('auth','ts-auth-mongo')):
    matches = [name for name in names if name.endswith('train-ticket-ts-'+service+'-mongo-1')]
    if len(matches) != 1:
        raise RuntimeError('Expected one '+service+' Mongo container')
    mongo = matches[0]
    archive = '/tmp/admin-user-'+service+'.archive'
    subprocess.run(['docker','exec',mongo,'mongodump','--db='+source,'--archive='+archive],check=True)
    subprocess.run(['docker','exec',mongo,'mongorestore','--archive='+archive,
                    '--nsFrom='+source+'.*','--nsTo=ts-admin-user-candidate.*','--drop'],check=True)

host = json.loads(subprocess.check_output(
    ['docker','inspect','station-migration-modulith-1'],text=True))[0]
env = dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(ADMIN_USER_ENABLED='true',USER_ENABLED='true',USER_WRITES_ENABLED='true',
           USER_MONGO_URI='mongodb://ts-user-mongo:27017/ts-admin-user-candidate',
           AUTH_ENABLED='true',AUTH_WRITES_ENABLED='true',
           AUTH_MONGO_URI='mongodb://ts-auth-mongo:27017/ts-admin-user-candidate',
           MODULITH_OWNERSHIP_FILE='')
file = root/'ts-modulith/target/admin-user-candidate.env'
file.write_text(''.join(k+'='+v+'\n' for k,v in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','admin-user-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18127:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:admin-user-candidate'],check=True)
print('Admin User candidate launched against isolated User and Auth snapshots')
