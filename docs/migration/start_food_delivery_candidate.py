"""Start Food Delivery against an isolated MySQL schema."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
name='food-delivery-module-candidate'
existing=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
if name in existing:
    raise RuntimeError(f'{name} already exists; inspect it before restarting')
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(FOOD_DELIVERY_ENABLED='true',FOOD_DELIVERY_WRITES_ENABLED='true',
           FOOD_DELIVERY_JDBC_URL='jdbc:mysql://ts-food-delivery-mysql:3306/food_delivery_candidate',
           FOOD_DELIVERY_DB_USER='root',FOOD_DELIVERY_DB_PASSWORD='root',
           MODULITH_OWNERSHIP_FILE='')
path=root/'ts-modulith/target/food-delivery-candidate.env'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name',name,'--network','train-ticket_my-network',
                '-p','127.0.0.1:18142:18080','--env-file',str(path),
                'train-ticket/ts-modulith:food-delivery-candidate'],check=True)
print('Food Delivery candidate started on 18142 with an isolated database')
