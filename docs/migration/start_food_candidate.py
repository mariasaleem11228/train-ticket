"""Launch isolated Food module and deployed legacy candidate against copied orders."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
env_file=root/'ts-modulith/target/food-candidate.env'
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in list(env):
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(FOOD_ENABLED='true',FOOD_WRITES_ENABLED='true',FOODMAP_ENABLED='true',
           FOOD_MONGO_URI='mongodb://ts-food-mongo:27017/food_candidate',
           FOOD_DELIVERY_QUEUE='food_delivery_candidate',MODULITH_OWNERSHIP_FILE='')
env_file.write_text(''.join(key+'='+value+'\n' for key,value in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','food-module-candidate','--network','train-ticket_my-network',
                '-p','127.0.0.1:18118:18080','--env-file',str(env_file),
                'train-ticket/ts-modulith:food-candidate'],check=True)
subprocess.run(['docker','run','-d','--name','food-legacy-candidate','--network','train-ticket_my-network',
                '-p','127.0.0.1:28856:18856',
                '-e','SPRING_DATA_MONGODB_HOST=ts-food-mongo',
                '-e','SPRING_DATA_MONGODB_DATABASE=food_legacy_test',
                '-e','JAVA_TOOL_OPTIONS=-XX:+UseSerialGC -Xmx192m',
                'codewisdom/ts-food-service:0.2.0'],check=True)
print('Food candidates launched')
