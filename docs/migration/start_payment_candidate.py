"""Run Payment against a separate Mongo database for transition checks."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
name='station-migration-payment-candidate-1'
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
environment=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in tuple(environment):
    if key.endswith('_WRITES_ENABLED'):environment[key]='false'
environment.update(PAYMENT_ENABLED='true',PAYMENT_WRITES_ENABLED='true',
                   PAYMENT_MONGO_URI='mongodb://ts-payment-mongo:27017/payment_module_migration_test')
environment.pop('MODULITH_OWNERSHIP_FILE',None)
path=root/'ts-modulith/target/payment-candidate.env'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in environment.items()),encoding='utf-8')
names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
if name in names:subprocess.run(['docker','rm','-f',name],check=True,capture_output=True)
subprocess.run(['docker','run','-d','--name',name,'--network','train-ticket_my-network',
                '-p','127.0.0.1:18110:18080','--env-file',str(path),
                'train-ticket/ts-modulith:payment-candidate'],check=True,capture_output=True)
print('Isolated Payment candidate started on http://127.0.0.1:18110')
