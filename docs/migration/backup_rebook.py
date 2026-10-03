"""Back up the live collections Rebook can change before cutover."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups'
backup.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for suffix,collection,archive in (
        ('train-ticket-ts-order-mongo-1','orders','rebook-orders.archive'),
        ('train-ticket-ts-order-other-mongo-1','orders','rebook-order-other.archive'),
        ('train-ticket-ts-inside-payment-mongo-1','payment','rebook-wallet-payment.archive')):
    matches=[name for name in names if name.endswith(suffix)]
    if len(matches)!=1:raise RuntimeError('Expected one Mongo container: '+suffix)
    name=matches[0]
    subprocess.run(['docker','exec',name,'mongodump','--db','ts','--collection',collection,
                    '--archive=/tmp/'+archive],check=True,capture_output=True)
    subprocess.run(['docker','cp',name+':/tmp/'+archive,str(backup/archive)],check=True,
                   capture_output=True)
    if (backup/archive).stat().st_size==0:raise RuntimeError('Empty backup: '+archive)
print('Rebook dependencies backed up: Orders, OrderOther and wallet payment')
