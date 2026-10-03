"""Back up the deployed Auth Mongo database before changing write ownership."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/auth.archive'
backup.parent.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-auth-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Auth Mongo container')
container=matches[0]
subprocess.run(['docker','exec',container,'mongodump','--db','ts-auth-mongo',
                '--archive=/tmp/auth.archive'],check=True)
subprocess.run(['docker','cp',container+':/tmp/auth.archive',str(backup)],check=True)
if backup.stat().st_size==0:raise RuntimeError('Auth backup is empty')
print('Auth database backed up to',backup)
