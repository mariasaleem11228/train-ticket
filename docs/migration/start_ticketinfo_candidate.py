"""Start the TicketInfo candidate beside the live legacy service."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
name='ticketinfo-module-candidate'
if name in subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines():
    raise RuntimeError(f'{name} already exists')
host=json.loads(subprocess.check_output(['docker','inspect','station-migration-modulith-1'],text=True))[0]
env=dict(item.split('=',1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):env[key]='false'
env.update(TICKETINFO_ENABLED='true',MODULITH_OWNERSHIP_FILE='',
           TRAVEL_TICKET_INFO_URL='http://127.0.0.1:9',
           TRAVEL2_TICKET_INFO_URL='http://127.0.0.1:9',
           PRESERVE_TICKET_INFO_URL='http://127.0.0.1:9',
           PRESERVE_OTHER_TICKET_INFO_URL='http://127.0.0.1:9')
path=root/'ts-modulith/target/ticketinfo-candidate.env'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in env.items()),encoding='utf-8')
subprocess.run(['docker','run','-d','--name',name,'--network','train-ticket_my-network',
                '-p','127.0.0.1:18143:18080','--env-file',str(path),
                'train-ticket/ts-modulith:ticketinfo-candidate'],check=True)
print('TicketInfo candidate started on 18143; legacy remains on 15681')
