"""Back up live Food orders before changing routing."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/food.archive'
backup.parent.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-food-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Food Mongo container')
container=matches[0]
subprocess.run(['docker','exec',container,'mongodump','--db','ts','--collection','foodorder',
                '--archive=/tmp/food.archive'],check=True)
subprocess.run(['docker','cp',container+':/tmp/food.archive',str(backup)],check=True)
if backup.stat().st_size==0:raise RuntimeError('Food backup empty')
print('Food orders backed up to',backup)
