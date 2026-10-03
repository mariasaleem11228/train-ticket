"""Back up the deployed User and Auth databases before changing User ownership."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup_dir=root/'deployment/migration/.state/backups'
backup_dir.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
for service,database in (('user','ts-user-mongo'),('auth','ts-auth-mongo')):
    matches=[name for name in names if name.endswith('train-ticket-ts-'+service+'-mongo-1')]
    if len(matches)!=1:raise RuntimeError('Expected one '+service+' Mongo container')
    container=matches[0]
    archive='/tmp/user-cutover-'+service+'.archive'
    backup=backup_dir/('user-cutover-'+service+'.archive')
    subprocess.run(['docker','exec',container,'mongodump','--db',database,
                    '--archive='+archive],check=True)
    subprocess.run(['docker','cp',container+':'+archive,str(backup)],check=True)
    if backup.stat().st_size==0:raise RuntimeError(service+' backup is empty')
    print(service+' database backed up to',backup)
