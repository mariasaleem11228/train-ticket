"""Start WaitOrder against an isolated schema, leaving the live host unchanged."""
import json
import subprocess
import time
from pathlib import Path

import hybrid_routing as routing
from http_support import wait_ready

name='wait-order-module-candidate'
routing.docker(*routing.COMPOSE,'up','-d','wait-order-mysql')
for attempt in range(60):
    result=subprocess.run(['docker','exec','station-migration-wait-order-mysql-1',
                           'mysql','-uroot','-proot','-e',
                           'CREATE DATABASE IF NOT EXISTS wait_order_candidate'],
                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if result.returncode==0:break
    time.sleep(2)
else:raise RuntimeError('WaitOrder MySQL did not become ready')
existing=routing.docker('ps','-a','--format','{{.Names}}').splitlines()
if name in existing:raise RuntimeError(name+' already exists; inspect it before restarting')
host=json.loads(routing.docker('inspect','station-migration-modulith-1'))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(WAIT_ORDER_ENABLED='true',WAIT_ORDER_WRITES_ENABLED='true',
           WAIT_ORDER_JDBC_URL='jdbc:mysql://ts-wait-order-mysql:3306/wait_order_candidate',
           WAIT_ORDER_DB_USER='root',WAIT_ORDER_DB_PASSWORD='root',MODULITH_OWNERSHIP_FILE='')
path=routing.ROOT/'ts-modulith/target/wait-order-candidate.env'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(''.join(f'{k}={v}\n' for k,v in env.items()),encoding='utf-8')
routing.docker('run','-d','--name',name,'--network','train-ticket_my-network',
               '-p','127.0.0.1:18144:18080','--env-file',str(path),
               'train-ticket/ts-modulith:wait-order-candidate')
wait_ready('http://127.0.0.1:18144','/actuator/health',seconds=180)
print('WaitOrder candidate ready on 18144')
