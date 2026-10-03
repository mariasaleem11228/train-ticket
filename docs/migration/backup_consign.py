"""Back up the live Consign collection before changing write ownership."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/consign.archive'
backup.parent.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-consign-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Consign Mongo container')
container=matches[0]
subprocess.run(['docker','exec',container,'mongodump','--db','ts','--collection','consign_record',
                '--archive=/tmp/consign.archive'],check=True)
subprocess.run(['docker','cp',container+':/tmp/consign.archive',str(backup)],check=True)
if backup.stat().st_size==0:raise RuntimeError('Consign backup is empty')
print('Consign collection backed up to',backup)
