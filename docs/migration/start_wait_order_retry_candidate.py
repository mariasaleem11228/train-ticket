"""Start retry candidate with isolated WaitOrder SQL and Orders Mongo databases."""
import json
import subprocess
from pathlib import Path

import hybrid_routing as routing
from http_support import wait_ready

name='wait-order-retry-candidate'
if name in routing.docker('ps','-a','--format','{{.Names}}').splitlines():
    raise RuntimeError(name+' already exists; inspect before replacing it')
routing.docker('exec','station-migration-wait-order-mysql-1','mysql','-uroot','-proot',
               '-e','CREATE DATABASE IF NOT EXISTS wait_order_retry_candidate')
host=json.loads(routing.docker('inspect','station-migration-modulith-1'))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(WAIT_ORDER_ENABLED='true',WAIT_ORDER_WRITES_ENABLED='true',
           WAIT_ORDER_RETRY_ENABLED='true',WAIT_ORDER_POLL_INTERVAL_MS='1000',
           WAIT_ORDER_JDBC_URL='jdbc:mysql://ts-wait-order-mysql:3306/wait_order_retry_candidate',
           ORDER_WRITES_ENABLED='true',PRESERVE_WRITES_ENABLED='true',
           ORDER_MONGO_URI='mongodb://ts-order-mongo:27017/wait_order_retry_candidate',
           MODULITH_OWNERSHIP_FILE='')
path=routing.ROOT/'ts-modulith/target/wait-order-retry-candidate.env'
path.write_text(''.join(f'{key}={value}\n' for key,value in env.items()),encoding='utf-8')
routing.docker('run','-d','--name',name,'--network','train-ticket_my-network',
               '-p','127.0.0.1:18145:18080','--env-file',str(path),
               'train-ticket/ts-modulith:wait-order-retry-candidate')
wait_ready('http://127.0.0.1:18145','/actuator/health',seconds=180)
print('WaitOrder retry candidate ready on port 18145; writes isolated')
