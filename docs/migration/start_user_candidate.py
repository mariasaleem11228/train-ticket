"""Start User beside the deployed service with isolated User and Auth databases."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for service,source,target in (('user','ts-user-mongo','ts-user-candidate'),
                              ('auth','ts-auth-mongo','ts-auth-user-candidate')):
    backup=root/('deployment/migration/.state/backups/user-cutover-'+service+'.archive')
    if not backup.exists() or backup.stat().st_size==0:raise RuntimeError(service+' backup required')
    matches=[name for name in names if name.endswith('train-ticket-ts-'+service+'-mongo-1')]
    if len(matches)!=1:raise RuntimeError('Expected one '+service+' Mongo container')
    mongo=matches[0]
    archive='/tmp/user-candidate-'+service+'.archive'
    subprocess.run(['docker','cp',str(backup),mongo+':'+archive],check=True)
    subprocess.run(['docker','exec',mongo,'mongorestore','--archive='+archive,
                    '--nsFrom='+source+'.*','--nsTo='+target+'.*','--drop'],check=True)

host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in list(env):
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(USER_ENABLED='true',USER_WRITES_ENABLED='true',
           USER_MONGO_URI='mongodb://ts-user-mongo:27017/ts-user-candidate',
           AUTH_ENABLED='true',AUTH_WRITES_ENABLED='true',
           AUTH_MONGO_URI='mongodb://ts-auth-mongo:27017/ts-auth-user-candidate',
           MODULITH_OWNERSHIP_FILE='')
file=root/'ts-modulith/target/user-candidate.env'
file.write_text(''.join(key+'='+value+'\n' for key,value in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','user-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18122:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:user-candidate'],check=True)
print('User candidate launched with isolated User and Auth snapshots')
