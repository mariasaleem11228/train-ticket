"""Back up the live ConsignPrice collection without altering its seeded records."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/consign-price.archive'
backup.parent.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-consign-price-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one ConsignPrice Mongo container')
container=matches[0]
subprocess.run(['docker','exec',container,'mongodump','--db','ts','--collection','consign_price',
                '--archive=/tmp/consign-price.archive'],check=True)
subprocess.run(['docker','cp',container+':/tmp/consign-price.archive',str(backup)],check=True)
if backup.stat().st_size==0:raise RuntimeError('ConsignPrice backup is empty')
print('ConsignPrice collection backed up to',backup)
