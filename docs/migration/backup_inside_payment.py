"""Back up both live Inside Payment collections before routing changes."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups'
backup.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-inside-payment-mongo-1')]
if len(matches)!=1:raise RuntimeError('Inside Payment Mongo container not found')
mongo=matches[0]
for collection in ('payment','addMoney'):
    archive='inside-payment-'+collection+'.archive'
    subprocess.run(['docker','exec',mongo,'mongodump','--db','ts','--collection',collection,
                    '--archive=/tmp/'+archive],check=True,capture_output=True)
    subprocess.run(['docker','cp',mongo+':/tmp/'+archive,str(backup/archive)],check=True,
                   capture_output=True)
    if (backup/archive).stat().st_size==0:raise RuntimeError('Empty backup: '+archive)
print('Inside Payment payment and addMoney collections backed up')
