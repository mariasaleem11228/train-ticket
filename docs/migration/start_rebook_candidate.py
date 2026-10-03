"""Run Rebook with isolated order and wallet databases."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
name='station-migration-rebook-candidate-1'
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
environment=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in tuple(environment):
    if key.endswith('_WRITES_ENABLED'):environment[key]='false'
environment.update(REBOOK_ENABLED='true',REBOOK_WRITES_ENABLED='true',
                   ORDER_WRITES_ENABLED='true',ORDER_OTHER_WRITES_ENABLED='true',
                   INSIDE_PAYMENT_WRITES_ENABLED='true',
                   ORDER_MONGO_URI='mongodb://ts-order-mongo:27017/rebook_orders_test',
                   ORDER_OTHER_MONGO_URI='mongodb://ts-order-other-mongo:27017/rebook_other_test',
                   INSIDE_PAYMENT_MONGO_URI='mongodb://ts-inside-payment-mongo:27017/rebook_wallet_test')
environment.pop('MODULITH_OWNERSHIP_FILE',None)
path=root/'ts-modulith/target/rebook-candidate.env'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in environment.items()),encoding='utf-8')
names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
if name in names:subprocess.run(['docker','rm','-f',name],check=True,capture_output=True)
subprocess.run(['docker','run','-d','--name',name,'--network','train-ticket_my-network',
                '-p','127.0.0.1:18113:18080','--env-file',str(path),
                'train-ticket/ts-modulith:rebook-candidate'],check=True,capture_output=True)
print('Isolated Rebook candidate started on http://127.0.0.1:18113')
