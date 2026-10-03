"""Verify the still-separate Food service consumes the routed Food Map module."""
import json
import urllib.request
from pathlib import Path

from http_support import request

root=Path(__file__).resolve().parents[2]
prefix='/api/v1/foodmapservice'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

with urllib.request.urlopen('http://127.0.0.1:18855'+prefix+'/trainfoods/D1345',timeout=20) as response:
    check('Food Map route points to module',response.status==200 and
          response.headers.get('X-FoodMap-Backend')=='module')
    trains=json.load(response)['data']
food_status,food=request('http://127.0.0.1:18856',
    '/api/v1/foodservice/foods/2026-10-03/Shang%20Hai/Su%20Zhou/D1345')
check('Food service returns composed menu',food_status==200 and food['status']==1 and
      food['msg']=='Get All Food Success')
check('Food service receives module train menu',food['data']['trainFoodList']==trains)
status,stores=request('http://127.0.0.1:18855',prefix+'/foodstores/suzhou')
check('Food service receives module station stores',status==200 and
      food['data']['foodStoreListMap']['suzhou']==stores['data'])
baseline=root/'ts-modulith/target/evidence/foodmap-food-baseline.json'
if baseline.exists():
    check('Food response matches pre-cutover baseline',
          {'status':food_status,'body':food}==json.loads(baseline.read_text()))
output=root/'ts-modulith/target/evidence/foodmap-integration.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Food Map integration passed')
