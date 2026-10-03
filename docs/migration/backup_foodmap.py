"""Back up both live Food Map collections before routing changes."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
backup=root/'deployment/migration/.state/backups/foodmap.archive'
backup.parent.mkdir(parents=True,exist_ok=True)
names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-food-map-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Food Map Mongo container')
container=matches[0]
subprocess.run(['docker','exec',container,'mongodump','--db','ts','--collection','stores',
                '--archive=/tmp/foodmap-stores.archive'],check=True)
subprocess.run(['docker','exec',container,'mongodump','--db','ts','--collection','trainfoods',
                '--archive=/tmp/foodmap-trainfoods.archive'],check=True)
for name in ('stores','trainfoods'):
    target=backup.with_name('foodmap-'+name+'.archive')
    subprocess.run(['docker','cp',container+':/tmp/foodmap-'+name+'.archive',str(target)],check=True)
    if target.stat().st_size==0:raise RuntimeError('Empty Food Map backup: '+name)
print('Food Map collections backed up')
