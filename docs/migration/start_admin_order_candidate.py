"""Run Admin Order beside legacy using isolated Orders and OrderOther copies."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
names = subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for service in ('order','order-other'):
    matches = [name for name in names if name.endswith('train-ticket-ts-'+service+'-mongo-1')]
    if len(matches) != 1:
        raise RuntimeError('Expected one '+service+' Mongo container')
    mongo = matches[0]
    archive = '/tmp/admin-order-'+service+'.archive'
    subprocess.run(['docker','exec',mongo,'mongodump','--db=ts','--archive='+archive],check=True)
    subprocess.run(['docker','exec',mongo,'mongorestore','--archive='+archive,
                    '--nsFrom=ts.*','--nsTo=ts-admin-order-candidate.*','--drop'],check=True)

host = json.loads(subprocess.check_output(
    ['docker','inspect','station-migration-modulith-1'],text=True))[0]
env = dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
for service,mongo in (('ORDER','order'),('ORDER_OTHER','order-other')):
    env[service+'_WRITES_ENABLED'] = 'true'
    env[service+'_MONGO_URI'] = ('mongodb://ts-'+mongo+'-mongo:27017/'
                                 'ts-admin-order-candidate')
env.update(ADMIN_ORDER_ENABLED='true',MODULITH_OWNERSHIP_FILE='')
file = root/'ts-modulith/target/admin-order-candidate.env'
file.write_text(''.join(k+'='+v+'\n' for k,v in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','admin-order-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18126:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:admin-order-candidate'],check=True)
print('Admin Order candidate launched against isolated order snapshots')
