"""Restore an isolated Auth snapshot and start the module beside legacy Auth."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/auth.archive'
if not backup.exists() or backup.stat().st_size==0:raise RuntimeError('Auth backup required')
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-auth-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Auth Mongo container')
mongo=matches[0]
subprocess.run(['docker','cp',str(backup),mongo+':/tmp/auth-candidate.archive'],check=True)
subprocess.run(['docker','exec',mongo,'mongorestore','--archive=/tmp/auth-candidate.archive',
                '--nsFrom=ts-auth-mongo.*','--nsTo=ts-auth-candidate.*','--drop'],check=True)
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in list(env):
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(AUTH_ENABLED='true',AUTH_WRITES_ENABLED='true',
           AUTH_MONGO_URI='mongodb://ts-auth-mongo:27017/ts-auth-candidate',
           MODULITH_OWNERSHIP_FILE='')
file=root/'ts-modulith/target/auth-candidate.env'
file.write_text(''.join(key+'='+value+'\n' for key,value in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','auth-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18121:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:auth-candidate'],check=True)
print('Auth candidate launched with isolated Mongo snapshot')
