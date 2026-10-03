"""Compare isolated deployed and module Notification APIs, mail and queue delivery."""
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from http_support import request

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:27853'
module='http://127.0.0.1:18119'
mailpit='http://127.0.0.1:18025'
prefix='/api/v1/notifyservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def mail():return json.load(urllib.request.urlopen(mailpit+'/api/v1/messages'))['messages']

def detail(id):return json.load(urllib.request.urlopen(mailpit+'/api/v1/message/'+id))

def mongo_count():
    command="db.getSiblingDB('notification_candidate').notifyInfo.countDocuments({})"
    return int(subprocess.check_output(['docker','exec','migration-infra-notification-mongo-1',
                                        'mongo','--quiet','--eval',command],text=True).strip())

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('28 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'notification'})
check('Notification is independent',graph['notification']['dependencies']==[])
check('welcome matches',request(legacy,prefix+'/welcome')==request(module,prefix+'/welcome'))
body={'email':'migration-notification@example.test','orderNumber':'test-123',
      'username':'Migration','startingPlace':'Shang Hai','endPlace':'Su Zhou',
      'startingTime':'10:00','date':'2026-10-03','seatClass':'1','seatNumber':'3A','price':'50'}
for kind in ('preserve_success','order_create_success','order_changed_success','order_cancel_success'):
    before={row['ID'] for row in mail()}
    legacy_result=request(legacy,prefix+'/notification/'+kind,'POST',body)
    legacy_new=[row for row in mail() if row['ID'] not in before]
    check(kind+' legacy sends mail',legacy_result==(200,True) and len(legacy_new)==1)
    module_result=request(module,prefix+'/notification/'+kind,'POST',body)
    module_new=[row for row in mail() if row['ID'] not in before and row['ID']!=legacy_new[0]['ID']]
    check(kind+' module sends mail',module_result==(200,True) and len(module_new)==1)
    first=detail(legacy_new[0]['ID']);second=detail(module_new[0]['ID'])
    check(kind+' subject and HTML match',first['Subject']==second['Subject'] and first['HTML']==second['HTML'])

failed=dict(body,email=None)
before_failure=len(mail())
check('invalid address returns false on both backends',
      request(legacy,prefix+'/notification/preserve_success','POST',failed)==(200,False) and
      request(module,prefix+'/notification/preserve_success','POST',failed)==(200,False) and
      len(mail())==before_failure)

before_count=mongo_count()
before_mail={row['ID'] for row in mail()}
queue_body=dict(body,email='migration-notification-queue@example.test',username='Queue')
helper=root/'docs/migration/publish_notification_candidate.py'
subprocess.run(['docker','run','--rm','--network','train-ticket_my-network',
                '-e','NOTIFICATION_TEST_PAYLOAD='+json.dumps(queue_body),
                '--mount',f'type=bind,source={helper},target=/work/publish.py,readonly',
                'python:3.13-alpine','sh','-c','pip install --quiet pika && python /work/publish.py'],check=True)
deadline=time.monotonic()+30
while time.monotonic()<deadline and (mongo_count()!=before_count+1 or len(mail())!=len(before_mail)+1):
    time.sleep(1)
check('candidate consumer saved one notification',mongo_count()==before_count+1)
queue_mail=[row for row in mail() if row['ID'] not in before_mail]
check('candidate consumer delivered to isolated SMTP',len(queue_mail)==1 and
      queue_mail[0]['Subject']=='Preserve Success' and
      queue_mail[0]['To'][0]['Address']==queue_body['email'])
output=root/'ts-modulith/target/evidence/notification-candidate.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Notification candidate comparison passed')
