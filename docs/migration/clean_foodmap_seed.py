"""Snapshot Food Map IDs, then remove only rows added during a legacy restart."""
import argparse
import json
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('action',choices=['snapshot','clean'])
parser.add_argument('snapshot',type=Path)
args=parser.parse_args()

names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
matches=[name for name in names if name.endswith('train-ticket-ts-food-map-mongo-1')]
if len(matches)!=1:raise RuntimeError('Expected one Food Map Mongo container')
container=matches[0]

def ids(collection):
    js='var rows=db.getSiblingDB("ts").getCollection("'+collection+'")'+\
       '.find({}, {_id:1}).toArray().map(function(x){return x._id.base64()});print(JSON.stringify(rows))'
    output=subprocess.check_output(['docker','exec',container,'mongo','--quiet','--eval',js],text=True)
    return json.loads(output.strip().splitlines()[-1])

if args.action=='snapshot':
    if args.snapshot.exists():raise RuntimeError('Snapshot already exists: '+str(args.snapshot))
    value={name:ids(name) for name in ('stores','trainfoods')}
    args.snapshot.parent.mkdir(parents=True,exist_ok=True)
    args.snapshot.write_text(json.dumps(value,indent=2),encoding='utf-8')
    print('Food Map IDs captured:',{key:len(value[key]) for key in value})
else:
    before=json.loads(args.snapshot.read_text())
    for collection,limit in [('stores',9),('trainfoods',5)]:
        original=set(before[collection]);current=set(ids(collection))
        if not original.issubset(current):raise RuntimeError('Preexisting Food Map rows missing')
        added=current-original
        if len(added) not in (0,limit):
            raise RuntimeError('Unexpected new Food Map rows; refusing cleanup: '+collection+' '+str(len(added)))
        if added:
            values=','.join('BinData(3,"'+value+'")' for value in sorted(added))
            js='var result=db.getSiblingDB("ts").getCollection("'+collection+'")'+\
               '.deleteMany({_id:{$in:['+values+']}});print(JSON.stringify({deleted:result.deletedCount}))'
            output=subprocess.check_output(['docker','exec',container,'mongo','--quiet','--eval',js],text=True)
            result=json.loads(output.strip().splitlines()[-1])
            if result['deleted']!=len(added):raise RuntimeError('Food Map cleanup count mismatch')
        print(collection,'removed',len(added),'startup rows; remaining',len(ids(collection)),flush=True)
