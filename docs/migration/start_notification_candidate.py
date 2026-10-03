"""Start Notification comparisons with isolated Mongo, queue and SMTP."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
target=root/'ts-modulith/target'
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in list(env):
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(NOTIFICATION_ENABLED='true',NOTIFICATION_WRITES_ENABLED='true',
           NOTIFICATION_MONGO_URI='mongodb://ts-notification-mongo:27017/notification_candidate',
           NOTIFICATION_QUEUE='email_candidate',NOTIFICATION_SMTP_HOST='notification-mailpit-candidate',
           MODULITH_OWNERSHIP_FILE='')
env_file=target/'notification-candidate.env'
env_file.write_text(''.join(key+'='+value+'\n' for key,value in env.items()),encoding='utf-8')
properties=target/'notification-legacy-candidate.properties'
properties.write_text('''spring.data.mongodb.host=ts-notification-mongo
spring.data.mongodb.database=notification_legacy_test
spring.rabbitmq.host=localhost
spring.rabbitmq.listener.simple.auto-startup=false
spring.mail.host=notification-mailpit-candidate
spring.mail.port=1025
spring.mail.username=
spring.mail.password=
spring.mail.properties.mail.smtp.auth=false
spring.mail.properties.mail.smtp.ssl.enable=false
spring.mail.properties.mail.smtp.starttls.enable=false
spring.mail.properties.mail.smtp.starttls.required=false
''',encoding='utf-8')
subprocess.run(['docker','run','-d','--name','notification-mailpit-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18025:8025',
                'axllent/mailpit@sha256:ed9b00c609e77e99c79b93f1178255ebc271868920f2c69a8d166bd5634ed10d'],check=True)
subprocess.run(['docker','run','-d','--name','notification-module-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:18119:18080',
                '--env-file',str(env_file),'train-ticket/ts-modulith:notification-candidate'],check=True)
subprocess.run(['docker','run','-d','--name','notification-legacy-candidate',
                '--network','train-ticket_my-network','-p','127.0.0.1:27853:17853',
                '-e','JAVA_TOOL_OPTIONS=-XX:+UseSerialGC -Xmx192m',
                '--mount',f'type=bind,source={properties},target=/config/application.properties,readonly',
                'codewisdom/ts-notification-service:0.2.0'],check=True)
print('Notification candidates launched')
