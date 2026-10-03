"""Run the deployed Python Voucher and the Java module on separate MySQL copies."""
import json
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
live = 'train-ticket-ts-voucher-mysql-1'
db = 'voucher-mysql-candidate'
existing = subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
if db not in existing:
    subprocess.run(['docker','run','-d','--name',db,'--network','train-ticket_my-network',
                    '-e','MYSQL_ROOT_PASSWORD=root','mysql'],check=True)
for attempt in range(60):
    ready = subprocess.run(['docker','exec',db,'mysql','-uroot','-proot','-e','SELECT 1'],
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if ready.returncode == 0: break
    time.sleep(2)
else: raise RuntimeError('Candidate MySQL did not start')

dump = subprocess.check_output(['docker','exec',live,'mysqldump','-uroot','-proot',
                                '--set-gtid-purged=OFF','--single-transaction','voucherservice'])
for name in ('voucherservice','voucher_module'):
    subprocess.run(['docker','exec',db,'mysql','-uroot','-proot','-e','CREATE DATABASE IF NOT EXISTS '+name],check=True)
    subprocess.run(['docker','exec','-i',db,'mysql','-uroot','-proot',name],input=dump,check=True)

database = json.loads(subprocess.check_output(['docker','inspect',db],text=True))[0]
ip = database['NetworkSettings']['Networks']['train-ticket_my-network']['IPAddress']
subprocess.run(['docker','run','-d','--name','voucher-legacy-candidate',
                '--network','train-ticket_my-network','--add-host','ts-voucher-mysql:'+ip,
                '-p','127.0.0.1:26101:16101','codewisdom/ts-voucher-service:0.2.0'],check=True)

host = json.loads(subprocess.check_output(
    ['docker','inspect','station-migration-modulith-1'],text=True))[0]
env = dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'): env[key] = 'false'
env.update(VOUCHER_ENABLED='true',VOUCHER_WRITES_ENABLED='true',
           VOUCHER_JDBC_URL='jdbc:mysql://voucher-mysql-candidate:3306/voucher_module',
           VOUCHER_DB_USER='root',VOUCHER_DB_PASSWORD='root',MODULITH_OWNERSHIP_FILE='')
file = root/'ts-modulith/target/voucher-candidate.env'
file.write_text(''.join(k+'='+v+'\n' for k,v in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name','voucher-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18128:18080',
                '--env-file',str(file),'train-ticket/ts-modulith:voucher-candidate'],check=True)
print('Voucher candidates started on separate copies of the live MySQL data')
