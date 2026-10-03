"""Compare all deployed Food Map API reads with the candidate module."""
import json
from pathlib import Path
from http_support import request

root=Path(__file__).resolve().parents[2]
live='http://127.0.0.1:18855'
module='http://127.0.0.1:18117'
prefix='/api/v1/foodmapservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('26 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'foodmap'})
check('Food Map has no module dependencies',graph['foodmap']['dependencies']==[])

for path in ['/trainfoods/welcome','/foodstores/welcome','/trainfoods',
             '/trainfoods/G1234','/trainfoods/D1345','/trainfoods/unknown',
             '/foodstores','/foodstores/shanghai','/foodstores/nanjing',
             '/foodstores/unknown']:
    check('GET '+path+' matches',request(live,prefix+path)==request(module,prefix+path))
for stations in [['shanghai','nanjing'],['unknown'],[]]:
    path=prefix+'/foodstores'
    check('POST /foodstores '+str(stations)+' matches',
          request(live,path,'POST',stations)==request(module,path,'POST',stations))

output=root/'ts-modulith/target/evidence/foodmap-candidate.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Food Map candidate passed')
