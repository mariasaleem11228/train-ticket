"""Read-only checkpoint checks; --rollback additionally probes the disabled writer.

The rollback probe targets only a cancelled synthetic order. Run after switching
Orders to legacy, then run without the flag after returning it to the module.
"""
import argparse
import base64
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rollback', action='store_true')
parser.add_argument('--legacy-framework', action='store_true',
                    help='Skip the Spring Modulith model check during an intentional host-image rollback')
args = parser.parse_args()
expected = 'legacy' if args.rollback else 'module'
results = []

def check(label, passed):
    results.append({'step': label, 'passed': bool(passed)})
    print('PASS' if passed else 'FAIL', label, flush=True)
    output = ROOT / ('ts-modulith/target/evidence/checkpoint-' + expected + '.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2))
    if not passed:
        raise AssertionError(label)

fixture = json.loads((ROOT / 'deployment/migration/.state/e2e/fixture.json').read_text())
routes=[
    ('Station', '/api/v1/stationservice/stations', 'module'),
    ('Orders', '/api/v1/orderservice/order/refresh', expected),
]
third=ROOT/'deployment/migration/.state/order-other-routing-state.json'
if third.exists() and json.loads(third.read_text())['mode'] in ('module','legacy'):
    routes.append(('OrderOther', '/api/v1/orderOtherService/orderOther/refresh',
                   json.loads(third.read_text())['mode']))
fourth=ROOT/'deployment/migration/.state/config-routing-state.json'
if fourth.exists() and json.loads(fourth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Config', '/api/v1/configservice/configs',
                   json.loads(fourth.read_text())['mode']))
fifth=ROOT/'deployment/migration/.state/seat-routing-state.json'
if fifth.exists() and json.loads(fifth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Seat', '/api/v1/seatservice/welcome',
                   json.loads(fifth.read_text())['mode']))
sixth=ROOT/'deployment/migration/.state/security-routing-state.json'
if sixth.exists() and json.loads(sixth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Security', '/api/v1/securityservice/securityConfigs',
                   json.loads(sixth.read_text())['mode']))
seventh=ROOT/'deployment/migration/.state/train-routing-state.json'
if seventh.exists() and json.loads(seventh.read_text())['mode'] in ('module','legacy'):
    routes.append(('Train', '/api/v1/trainservice/trains',
                   json.loads(seventh.read_text())['mode']))
eighth=ROOT/'deployment/migration/.state/route-routing-state.json'
if eighth.exists() and json.loads(eighth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Route', '/api/v1/routeservice/routes',
                   json.loads(eighth.read_text())['mode']))
ninth=ROOT/'deployment/migration/.state/price-routing-state.json'
if ninth.exists() and json.loads(ninth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Price', '/api/v1/priceservice/prices',
                   json.loads(ninth.read_text())['mode']))
tenth=ROOT/'deployment/migration/.state/basic-routing-state.json'
if tenth.exists() and json.loads(tenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Basic', '/api/v1/basicservice/welcome',
                   json.loads(tenth.read_text())['mode']))
eleventh=ROOT/'deployment/migration/.state/travel-routing-state.json'
if eleventh.exists() and json.loads(eleventh.read_text())['mode'] in ('module','legacy'):
    routes.append(('Travel', '/api/v1/travelservice/trips',
                   json.loads(eleventh.read_text())['mode']))
twelfth=ROOT/'deployment/migration/.state/travel2-routing-state.json'
if twelfth.exists() and json.loads(twelfth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Travel2', '/api/v1/travel2service/trips',
                   json.loads(twelfth.read_text())['mode']))
thirteenth=ROOT/'deployment/migration/.state/route-plan-routing-state.json'
if thirteenth.exists() and json.loads(thirteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('RoutePlan', '/api/v1/routeplanservice/welcome',
                   json.loads(thirteenth.read_text())['mode']))
fourteenth=ROOT/'deployment/migration/.state/travel-plan-routing-state.json'
if fourteenth.exists() and json.loads(fourteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('TravelPlan', '/api/v1/travelplanservice/welcome',
                   json.loads(fourteenth.read_text())['mode']))
fifteenth=ROOT/'deployment/migration/.state/contacts-routing-state.json'
if fifteenth.exists() and json.loads(fifteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Contacts', '/api/v1/contactservice/contacts',
                   json.loads(fifteenth.read_text())['mode']))
sixteenth=ROOT/'deployment/migration/.state/preserve-routing-state.json'
if sixteenth.exists() and json.loads(sixteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Preserve', '/api/v1/preserveservice/welcome',
                   json.loads(sixteenth.read_text())['mode']))
seventeenth=ROOT/'deployment/migration/.state/preserve-other-routing-state.json'
if seventeenth.exists() and json.loads(seventeenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('PreserveOther', '/api/v1/preserveotherservice/welcome',
                   json.loads(seventeenth.read_text())['mode']))
eighteenth=ROOT/'deployment/migration/.state/execute-routing-state.json'
if eighteenth.exists() and json.loads(eighteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Execute', '/api/v1/executeservice/welcome',
                   json.loads(eighteenth.read_text())['mode']))
nineteenth=ROOT/'deployment/migration/.state/payment-routing-state.json'
if nineteenth.exists() and json.loads(nineteenth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Payment', '/api/v1/paymentservice/welcome',
                   json.loads(nineteenth.read_text())['mode']))
twentieth=ROOT/'deployment/migration/.state/inside-payment-routing-state.json'
if twentieth.exists() and json.loads(twentieth.read_text())['mode'] in ('module','legacy'):
    routes.append(('InsidePayment', '/api/v1/inside_pay_service/welcome',
                   json.loads(twentieth.read_text())['mode']))
twenty_first=ROOT/'deployment/migration/.state/cancel-routing-state.json'
if twenty_first.exists() and json.loads(twenty_first.read_text())['mode'] in ('module','legacy'):
    routes.append(('Cancel', '/api/v1/cancelservice/welcome',
                   json.loads(twenty_first.read_text())['mode']))
twenty_second=ROOT/'deployment/migration/.state/rebook-routing-state.json'
if twenty_second.exists() and json.loads(twenty_second.read_text())['mode'] in ('module','legacy'):
    routes.append(('Rebook', '/api/v1/rebookservice/welcome',
                   json.loads(twenty_second.read_text())['mode']))
twenty_third=ROOT/'deployment/migration/.state/assurance-routing-state.json'
if twenty_third.exists() and json.loads(twenty_third.read_text())['mode'] in ('module','legacy'):
    routes.append(('Assurance', '/api/v1/assuranceservice/welcome',
                   json.loads(twenty_third.read_text())['mode']))
twenty_fourth=ROOT/'deployment/migration/.state/consign-price-routing-state.json'
if twenty_fourth.exists() and json.loads(twenty_fourth.read_text())['mode'] in ('module','legacy'):
    routes.append(('ConsignPrice', '/api/v1/consignpriceservice/welcome',
                   json.loads(twenty_fourth.read_text())['mode']))
twenty_fifth=ROOT/'deployment/migration/.state/consign-routing-state.json'
if twenty_fifth.exists() and json.loads(twenty_fifth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Consign', '/api/v1/consignservice/welcome',
                   json.loads(twenty_fifth.read_text())['mode']))
twenty_sixth=ROOT/'deployment/migration/.state/foodmap-routing-state.json'
if twenty_sixth.exists() and json.loads(twenty_sixth.read_text())['mode'] in ('module','legacy'):
    routes.append(('FoodMap', '/api/v1/foodmapservice/trainfoods/welcome',
                   json.loads(twenty_sixth.read_text())['mode']))
twenty_seventh=ROOT/'deployment/migration/.state/food-routing-state.json'
if twenty_seventh.exists() and json.loads(twenty_seventh.read_text())['mode'] in ('module','legacy'):
    routes.append(('Food', '/api/v1/foodservice/welcome',
                   json.loads(twenty_seventh.read_text())['mode']))
twenty_eighth=ROOT/'deployment/migration/.state/notification-routing-state.json'
if twenty_eighth.exists() and json.loads(twenty_eighth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Notification', '/api/v1/notifyservice/welcome',
                   json.loads(twenty_eighth.read_text())['mode']))
twenty_ninth=ROOT/'deployment/migration/.state/verifycode-routing-state.json'
if twenty_ninth.exists() and json.loads(twenty_ninth.read_text())['mode'] in ('module','legacy'):
    routes.append(('VerifyCode', '/api/v1/verifycode/verify/WRONG',
                   json.loads(twenty_ninth.read_text())['mode']))
thirtieth=ROOT/'deployment/migration/.state/auth-routing-state.json'
if thirtieth.exists() and json.loads(thirtieth.read_text())['mode'] in ('module','legacy'):
    routes.append(('Auth', '/api/v1/auth/hello',
                   json.loads(thirtieth.read_text())['mode']))
thirty_first=ROOT/'deployment/migration/.state/user-routing-state.json'
if thirty_first.exists() and json.loads(thirty_first.read_text())['mode'] in ('module','legacy'):
    routes.append(('User', '/api/v1/userservice/users/hello',
                   json.loads(thirty_first.read_text())['mode']))
thirty_second=ROOT/'deployment/migration/.state/admin-basic-routing-state.json'
if thirty_second.exists() and json.loads(thirty_second.read_text())['mode'] in ('module','legacy'):
    routes.append(('AdminBasic', '/api/v1/adminbasicservice/adminbasic/contacts',
                   json.loads(thirty_second.read_text())['mode']))
thirty_third=ROOT/'deployment/migration/.state/admin-route-routing-state.json'
if thirty_third.exists() and json.loads(thirty_third.read_text())['mode'] in ('module','legacy'):
    routes.append(('AdminRoute', '/api/v1/adminrouteservice/welcome',
                   json.loads(thirty_third.read_text())['mode']))
thirty_fourth=ROOT/'deployment/migration/.state/admin-travel-routing-state.json'
if thirty_fourth.exists() and json.loads(thirty_fourth.read_text())['mode'] in ('module','legacy'):
    routes.append(('AdminTravel', '/api/v1/admintravelservice/welcome',
                   json.loads(thirty_fourth.read_text())['mode']))
thirty_fifth=ROOT/'deployment/migration/.state/admin-order-routing-state.json'
if thirty_fifth.exists() and json.loads(thirty_fifth.read_text())['mode'] in ('module','legacy'):
    routes.append(('AdminOrder', '/api/v1/adminorderservice/welcome',
                   json.loads(thirty_fifth.read_text())['mode']))
thirty_sixth=ROOT/'deployment/migration/.state/admin-user-routing-state.json'
if thirty_sixth.exists() and json.loads(thirty_sixth.read_text())['mode'] in ('module','legacy'):
    routes.append(('AdminUser', '/api/v1/adminuserservice/users/welcome',
                   json.loads(thirty_sixth.read_text())['mode']))
thirty_seventh=ROOT/'deployment/migration/.state/voucher-routing-state.json'
thirty_eighth=ROOT/'deployment/migration/.state/news-routing-state.json'
thirty_ninth=ROOT/'deployment/migration/.state/ticket-office-routing-state.json'
fortieth=ROOT/'deployment/migration/.state/avatar-routing-state.json'
for name, path, backend in routes:
    body = None if name in ('Station','Config','Seat','Security','Train','Route','Price','Basic','Travel','Travel2','RoutePlan','TravelPlan','Contacts','Preserve','PreserveOther','Execute','Payment','InsidePayment','Cancel','Rebook','Assurance','ConsignPrice','Consign','FoodMap','Food','Notification','VerifyCode','Auth','User','AdminBasic','AdminRoute','AdminTravel','AdminOrder','AdminUser') else json.dumps({'loginId': fixture['userId'],
        'enableStateQuery': False, 'enableTravelDateQuery': False, 'enableBoughtDateQuery': False}).encode()
    base = 'http://localhost:16115' if name == 'AdminUser' else \
           'http://localhost:16112' if name == 'AdminOrder' else \
           'http://localhost:16114' if name == 'AdminTravel' else \
           'http://localhost:16113' if name == 'AdminRoute' else \
           'http://localhost:18767' if name == 'AdminBasic' else \
           'http://localhost:12342' if name == 'User' else \
           'http://localhost:12340' if name == 'Auth' else \
           'http://localhost:15678' if name == 'VerifyCode' else \
           'http://localhost:17853' if name == 'Notification' else \
           'http://localhost:18856' if name == 'Food' else \
           'http://localhost:18855' if name == 'FoodMap' else \
           'http://localhost:16111' if name == 'Consign' else \
           'http://localhost:16110' if name == 'ConsignPrice' else \
           'http://localhost:18888' if name == 'Assurance' else \
           'http://localhost:18886' if name == 'Rebook' else \
           'http://localhost:18885' if name == 'Cancel' else \
           'http://localhost:18673' if name == 'InsidePayment' else \
           'http://localhost:19001' if name == 'Payment' else \
           'http://localhost:12386' if name == 'Execute' else \
           'http://localhost:14569' if name == 'PreserveOther' else \
           'http://localhost:14568' if name == 'Preserve' else \
           'http://localhost:12347' if name == 'Contacts' else \
           'http://localhost:14322' if name == 'TravelPlan' else \
           'http://localhost:14578' if name == 'RoutePlan' else \
           'http://localhost:16346' if name == 'Travel2' else \
           'http://localhost:12346' if name == 'Travel' else \
           'http://localhost:15680' if name == 'Basic' else \
           'http://localhost:18898' if name == 'Seat' else \
           'http://localhost:11188' if name == 'Security' else \
           'http://localhost:14567' if name == 'Train' else \
           'http://localhost:11178' if name == 'Route' else \
           'http://localhost:16579' if name == 'Price' else 'http://localhost:8080'
    req = urllib.request.Request(base + path, data=body,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' +
                 test_token('ROLE_USER' if name == 'Assurance' else 'ROLE_ADMIN')})
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = response.read().decode()
        check(name + (' service' if name in ('Seat','Security','Train','Route','Price','Basic','Travel','Travel2','RoutePlan','TravelPlan','Contacts','Preserve','PreserveOther','Execute','Payment','InsidePayment','Cancel','Rebook','Assurance','ConsignPrice','Consign','FoodMap','Food','Notification','VerifyCode','Auth','User','AdminBasic','AdminRoute','AdminTravel','AdminOrder','AdminUser') else ' UI') + ' route and backend', response.status == 200
              and response.headers.get('X-' + name + '-Backend') == backend
              and (payload == 'Hello' if name == 'User'
                   else payload == 'hello' if name == 'Auth'
                   else payload == 'true' if name == 'VerifyCode'
                   else payload == 'Welcome to [ Notification Service ] !' if name == 'Notification'
                   else payload == 'Welcome to [ Food Service ] !' if name == 'Food'
                   else payload == 'Welcome to [ Train Food Service ] !' if name == 'FoodMap'
                   else payload == 'Welcome to [ Consign Service ] !' if name == 'Consign'
                   else payload == 'Welcome to [ ConsignPrice Service ] !' if name == 'ConsignPrice'
                   else payload == 'Welcome to [ Assurance Service ] !' if name == 'Assurance'
                   else payload == 'Welcome to [ Rebook Service ] !' if name == 'Rebook'
                   else payload == 'Welcome to [ Cancel Service ] !' if name == 'Cancel'
                   else payload == 'Welcome to [ InsidePayment Service ] !' if name == 'InsidePayment'
                   else payload == 'Welcome to [ Payment Service ] !' if name == 'Payment'
                   else payload == 'Welcome to [ Execute Service ] !' if name == 'Execute'
                   else payload == 'Welcome to [ PreserveOther Service ] !' if name == 'PreserveOther'
                   else payload == 'Welcome to [ Preserve Service ] !' if name == 'Preserve'
                   else payload == 'Welcome to [ TravelPlan Service ] !' if name == 'TravelPlan'
                   else payload == 'Welcome to [ RoutePlan Service ] !' if name == 'RoutePlan'
                   else payload == 'Welcome to [ Seat Service ] !' if name == 'Seat'
                   else payload == 'Welcome to [ Basic Service ] !' if name == 'Basic'
                   else payload == 'Welcome to [ AdminRoute Service ] !' if name == 'AdminRoute'
                   else payload == 'Welcome to [ AdminTravel Service ] !' if name == 'AdminTravel'
                   else payload == 'Welcome to [Admin Order Service] !' if name == 'AdminOrder'
                   else payload == 'Welcome to [ AdminUser Service ] !' if name == 'AdminUser'
                   else json.loads(payload)['status'] == 1))
if thirty_seventh.exists() and json.loads(thirty_seventh.read_text())['mode'] in ('module','legacy'):
    voucher_mode=json.loads(thirty_seventh.read_text())['mode']
    try:
        urllib.request.urlopen('http://localhost:8080/getVoucher',timeout=20)
    except urllib.error.HTTPError as error:
        check('Voucher UI route and backend',error.code==405 and
              error.headers.get('X-Voucher-Backend')==voucher_mode)
    else:
        check('Voucher UI route rejects GET',False)
    voucher_fixture=ROOT/'deployment/migration/.state/e2e/voucher.json'
    if voucher_fixture.exists():
        order_id=json.loads(voucher_fixture.read_text())['orderId']
        kind=json.loads(voucher_fixture.read_text())['type']
        req=urllib.request.Request('http://localhost:8080/getVoucher',
            data=json.dumps({'orderId':order_id,'type':kind}).encode(),
            headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=20) as response:
            body=json.load(response)
            check('synthetic Voucher retained',response.status==200 and
                  response.headers.get('X-Voucher-Backend')==voucher_mode and
                  body['order_id']==order_id)
if thirty_eighth.exists() and json.loads(thirty_eighth.read_text())['mode'] in ('module','legacy'):
    news_mode=json.loads(thirty_eighth.read_text())['mode']
    with urllib.request.urlopen('http://localhost:8080/news-service/news',timeout=20) as response:
        body=response.read()
        with urllib.request.urlopen('http://localhost:12862/news-service/news',timeout=20) as direct:
            check('News UI route and backend',response.status==200 and
                  response.headers.get('X-News-Backend')==news_mode and
                  response.headers.get('Content-Type').replace(' ','').lower()==
                  direct.headers.get('Content-Type').replace(' ','').lower() and
                  body==direct.read() and b'News Service Complete' in body)
if thirty_ninth.exists() and json.loads(thirty_ninth.read_text())['mode'] in ('module','legacy'):
    office_mode=json.loads(thirty_ninth.read_text())['mode']
    with urllib.request.urlopen('http://localhost:8080/office/getRegionList',timeout=20) as response:
        regions=json.load(response)
        check('Ticket Office UI route and backend',response.status==200 and
              response.headers.get('X-TicketOffice-Backend')==office_mode and
              any(row.get('province')=='Shanghai' for row in regions))
if fortieth.exists() and json.loads(fortieth.read_text())['mode'] in ('module','legacy'):
    avatar_mode=json.loads(fortieth.read_text())['mode']
    face=base64.b64encode((ROOT/'ts-avatar-service/images/test.png').read_bytes()).decode()
    req=urllib.request.Request('http://localhost:8080/api/v1/avatar',
        data=json.dumps({'img':face}).encode(),
        headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=40) as response:
        body=response.read()
        check('Avatar UI route and face crop',response.status==200 and
              response.headers.get('X-Avatar-Backend')==avatar_mode and
              hashlib.sha256(body).hexdigest()==
              'b2b3923b58e078a56696d27968414baf65b3b7c81c90be32c609a150c9010d7a')
if nineteenth.exists() and json.loads(nineteenth.read_text())['mode'] in ('module','legacy'):
    payment_path='/api/v1/paymentservice/payment'
    check('Payment denies unauthenticated reads',
          request('http://localhost:19001',payment_path)[0]==403)
    check('Payment accepts user role',
          request('http://localhost:19001',payment_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twentieth.exists() and json.loads(twentieth.read_text())['mode'] in ('module','legacy'):
    inside_path='/api/v1/inside_pay_service/inside_payment/payment'
    check('Inside Payment denies unauthenticated reads',
          request('http://localhost:18673',inside_path)[0]==403)
    check('Inside Payment accepts user role',
          request('http://localhost:18673',inside_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twenty_first.exists() and json.loads(twenty_first.read_text())['mode'] in ('module','legacy'):
    cancel_path='/api/v1/cancelservice/cancel/refound/00000000-0000-0000-0000-000000000000'
    check('Cancel denies unauthenticated reads',
          request('http://localhost:18885',cancel_path)[0]==403)
    check('Cancel accepts user role',
          request('http://localhost:18885',cancel_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twenty_second.exists() and json.loads(twenty_second.read_text())['mode'] in ('module','legacy'):
    rebook_path='/api/v1/rebookservice/welcome'
    check('Rebook denies unauthenticated requests',
          request('http://localhost:18886',rebook_path)[0]==403)
    check('Rebook accepts user role',
          request('http://localhost:18886',rebook_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twenty_third.exists() and json.loads(twenty_third.read_text())['mode'] in ('module','legacy'):
    assurance_path='/api/v1/assuranceservice/assurances/types'
    check('Assurance denies unauthenticated requests',
          request('http://localhost:18888',assurance_path)[0]==403)
    check('Assurance accepts user role',
          request('http://localhost:18888',assurance_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twenty_fourth.exists() and json.loads(twenty_fourth.read_text())['mode'] in ('module','legacy'):
    consign_price_path='/api/v1/consignpriceservice/consignprice/2/true'
    check('ConsignPrice denies unauthenticated requests',
          request('http://localhost:16110',consign_price_path)[0]==403)
    check('ConsignPrice accepts user role',
          request('http://localhost:16110',consign_price_path,
                  token=test_token('ROLE_USER'))[0]==200)
if twenty_fifth.exists() and json.loads(twenty_fifth.read_text())['mode'] in ('module','legacy'):
    consign_path='/api/v1/consignservice/welcome'
    check('Consign denies unauthenticated requests',
          request('http://localhost:16111',consign_path)[0]==403)
    check('Consign accepts user role',
          request('http://localhost:16111',consign_path,
                  token=test_token('ROLE_USER'))[0]==200)
if thirtieth.exists() and json.loads(thirtieth.read_text())['mode'] in ('module','legacy'):
    auth_base='http://localhost:12340'
    check('Auth rejects incorrect password',request(auth_base,'/api/v1/users/login','POST',
          {'username':'fdse_microservice','password':'WRONG','verificationCode':''})[1]['status']==0)
    status,login=request(auth_base,'/api/v1/users/login','POST',
                         {'username':'fdse_microservice','password':'111111','verificationCode':'WRONG'})
    check('Auth issues compatible token through Verification Code',status==200 and
          login['status']==1 and login['data']['userId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f' and
          request('http://localhost:18080','/api/v1/paymentservice/welcome',
                  token=login['data']['token'])[0]==200)
if thirty_first.exists() and json.loads(thirty_first.read_text())['mode'] in ('module','legacy'):
    status,profile=request('http://localhost:12342',
                           '/api/v1/userservice/users/fdse_microservice')
    check('User reads existing profile',status==200 and profile['status']==1 and
          profile['data']['userId']=='4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f')
    status,admin_users=request('http://localhost:16115','/api/v1/adminuserservice/users',
                               token=test_token('ROLE_ADMIN'))
    check('running Admin User reads User route',status==200 and admin_users['status']==1 and
          any(row['userName']=='fdse_microservice' for row in admin_users['data']))
status, data = request('http://localhost:18080', '/actuator/health')
check('shared host health', status == 200 and data['status'] == 'UP')
if not args.legacy_framework:
    status, modules = request('http://localhost:18080', '/actuator/modulith')
    expected_modules = set(json.loads((ROOT/'deployment/migration/.state/hybrid.json').read_text())['modules'])
    check('Spring Modulith reports expected business modules', status == 200
          and isinstance(modules, dict) and set(modules) == expected_modules)
    check('Orders and OrderOther depend on Station', all(
            {dependency['target'] for dependency in modules[name]['dependencies']} == {'station'}
            for name in ('orders', 'orderother')) and modules['station']['dependencies'] == [])
    if 'config' in expected_modules:
        check('Config is an independent Spring Modulith module', modules['config']['dependencies'] == [])
    if 'seat' in expected_modules:
        check('Seat uses its published providers',
              {edge['target'] for edge in modules['seat']['dependencies']} ==
              {'orders', 'orderother', 'config'} |
              ({'tripcatalog', 'route', 'train'} if 'tripcatalog' in expected_modules else set()))
    if 'security' in expected_modules:
        check('Security uses Orders and OrderOther',
              {edge['target'] for edge in modules['security']['dependencies']} ==
              {'orders', 'orderother'})
    if 'train' in expected_modules:
        check('Train is an independent Spring Modulith module', modules['train']['dependencies'] == [])
    if 'route' in expected_modules:
        check('Route is an independent Spring Modulith module', modules['route']['dependencies'] == [])
    if 'price' in expected_modules:
        check('Price is an independent Spring Modulith module', modules['price']['dependencies'] == [])
    if 'basic' in expected_modules:
        check('Basic uses Station, Train, Route and Price',
              {edge['target'] for edge in modules['basic']['dependencies']} ==
              {'station', 'train', 'route', 'price'})
    if 'travel' in expected_modules:
        check('Travel uses its published providers',
              {edge['target'] for edge in modules['travel']['dependencies']} ==
              {'train', 'route', 'orders', 'seat'} |
              ({'ticketinfo'} if 'ticketinfo' in expected_modules else set()) |
              ({'tripcatalog'} if 'tripcatalog' in expected_modules else set()))
    if 'travel2' in expected_modules:
        check('Travel2 uses its published providers',
              {edge['target'] for edge in modules['travel2']['dependencies']} ==
              {'train', 'route', 'orders', 'seat'} |
              ({'ticketinfo'} if 'ticketinfo' in expected_modules else set()) |
              ({'tripcatalog'} if 'tripcatalog' in expected_modules else set()))
    if 'tripcatalog' in expected_modules:
        check('Trip Catalog owns trip persistence without module dependencies',
              modules['tripcatalog']['dependencies'] == [])
    if 'routeplan' in expected_modules:
        check('Route Plan uses Station, Route, Travel and Travel2',
              {edge['target'] for edge in modules['routeplan']['dependencies']} ==
              {'station', 'route', 'travel', 'travel2'})
    if 'travelplan' in expected_modules:
        check('Travel Plan uses Station, Seat, Travel, Travel2 and Route Plan',
              {edge['target'] for edge in modules['travelplan']['dependencies']} ==
              {'station', 'seat', 'travel', 'travel2', 'routeplan'})
    if 'contacts' in expected_modules:
        check('Contacts is an independent Spring Modulith module',
              modules['contacts']['dependencies'] == [])
    if 'preserveother' in expected_modules:
        check('PreserveOther uses its published providers',
              {edge['target'] for edge in modules['preserveother']['dependencies']} ==
              {'security', 'contacts', 'travel2', 'station', 'seat', 'orderother',
               'user', 'assurance', 'food', 'consign'} |
              ({'ticketinfo'} if 'ticketinfo' in expected_modules else set()))
    if 'execute' in expected_modules:
        check('Execute uses Orders and OrderOther',
              {edge['target'] for edge in modules['execute']['dependencies']} ==
              {'orders', 'orderother'})
    if 'payment' in expected_modules:
        check('Payment is an independent Spring Modulith module',
              modules['payment']['dependencies'] == [])
    if 'insidepayment' in expected_modules:
        check('Inside Payment uses Orders, OrderOther and Payment',
              {edge['target'] for edge in modules['insidepayment']['dependencies']} ==
              {'orders','orderother','payment'})
    if 'cancel' in expected_modules:
        check('Cancel uses Orders, OrderOther, Inside Payment and User',
              {edge['target'] for edge in modules['cancel']['dependencies']} ==
              {'orders','orderother','insidepayment','user'})
    if 'rebook' in expected_modules:
        check('Rebook uses seven published modules',
              {edge['target'] for edge in modules['rebook']['dependencies']} ==
              {'orders','orderother','station','travel','travel2','seat','insidepayment'})
    if 'assurance' in expected_modules:
        check('Assurance is an independent Spring Modulith module',
              modules['assurance']['dependencies'] == [])
    if 'consignprice' in expected_modules:
        check('ConsignPrice is an independent Spring Modulith module',
              modules['consignprice']['dependencies'] == [])
    if 'consign' in expected_modules:
        check('Consign uses ConsignPrice through its published API',
              {edge['target'] for edge in modules['consign']['dependencies']} == {'consignprice'})
    if 'foodmap' in expected_modules:
        check('Food Map is an independent Spring Modulith module',
              modules['foodmap']['dependencies'] == [])
    if 'food' in expected_modules:
        check('Food uses Food Map, Travel, Station and Route',
              {edge['target'] for edge in modules['food']['dependencies']} ==
              {'foodmap','travel','station','route'})
    if 'notification' in expected_modules:
        check('Notification is an independent Spring Modulith module',
              modules['notification']['dependencies'] == [])
    if 'verifycode' in expected_modules:
        check('Verification Code is an independent Spring Modulith module',
              modules['verifycode']['dependencies'] == [])
    if 'auth' in expected_modules:
        check('Auth uses Verification Code through its published API',
              {edge['target'] for edge in modules['auth']['dependencies']} == {'verifycode'})
    if 'user' in expected_modules:
        check('User uses Auth through its published API',
              {edge['target'] for edge in modules['user']['dependencies']} == {'auth'})
    if 'adminbasic' in expected_modules:
        check('Admin Basic Info uses five published catalogue APIs',
              {edge['target'] for edge in modules['adminbasic']['dependencies']} ==
              {'contacts','station','train','config','price'})
    if 'adminroute' in expected_modules:
        check('Admin Route uses the published Route API',
              {edge['target'] for edge in modules['adminroute']['dependencies']} == {'route'})
    if 'admintravel' in expected_modules:
        check('Admin Travel uses the published Travel APIs',
              {edge['target'] for edge in modules['admintravel']['dependencies']} == {'travel','travel2'})
    if 'adminorder' in expected_modules:
        check('Admin Order uses the published Order APIs',
              {edge['target'] for edge in modules['adminorder']['dependencies']} == {'orders','orderother'})
    if 'adminuser' in expected_modules:
        check('Admin User uses the published User API',
              {edge['target'] for edge in modules['adminuser']['dependencies']} == {'user'})
    if 'voucher' in expected_modules:
        check('Voucher uses the published Order APIs',
              {edge['target'] for edge in modules['voucher']['dependencies']} == {'orders','orderother'})
    if 'news' in expected_modules:
        check('News is an independent Spring Modulith module',
              modules['news']['dependencies'] == [])
    if 'ticketoffice' in expected_modules:
        check('Ticket Office is an independent Spring Modulith module',
              modules['ticketoffice']['dependencies'] == [])
    if 'avatar' in expected_modules:
        check('Avatar is an independent Spring Modulith module',
              modules['avatar']['dependencies'] == [])
    if 'delivery' in expected_modules:
        check('Delivery is an independent Spring Modulith module',
              modules['delivery']['dependencies'] == [])
    if 'fooddelivery' in expected_modules:
        check('Food Delivery uses Food Map through its published API',
              {dependency['target'] for dependency in modules['fooddelivery']['dependencies']} == {'foodmap'})
    if 'ticketinfo' in expected_modules:
        check('TicketInfo uses Basic and Station published APIs',
              {dependency['target'] for dependency in modules['ticketinfo']['dependencies']} == {'basic', 'station'})
    if 'waitorder' in expected_modules:
        check('WaitOrder uses Preserve through a published module API',
              {dependency['target'] for dependency in modules['waitorder']['dependencies']} == {'preserve'})
    if 'preserve' in expected_modules:
        check('Preserve uses its published providers',
              {edge['target'] for edge in modules['preserve']['dependencies']} ==
              {'security', 'contacts', 'travel', 'station', 'seat', 'orders',
               'user', 'assurance', 'food', 'consign'} |
              ({'ticketinfo'} if 'ticketinfo' in expected_modules else set()))
fixture = json.loads((ROOT / 'deployment/migration/.state/e2e/fixture.json').read_text())
for order in fixture['testOrders']:
    status, data = request('http://localhost:12031', '/api/v1/orderservice/order/' + order['id'], token=test_token())
    check('synthetic order retained from ' + order['stage'], status == 200
          and data['status'] == 1 and data['data']['status'] == 4)
for order in fixture.get('testOtherOrders',[]):
    status,data=request('http://localhost:12032','/api/v1/orderOtherService/orderOther/'+order['id'],token=test_token())
    check('synthetic OrderOther booking retained',status==200 and data['status']==1
          and data['data']['status']==4)
if args.rollback:
    order_id = fixture['testOrders'][-1]['id']
    path = '/api/v1/orderservice/order/' + order_id
    before = request('http://localhost:12031', path, token=test_token())
    status, _ = request('http://localhost:18080', '/api/v1/orderservice/order/orderPay/' + order_id, token=test_token())
    check('Orders module rejects writes during rollback', status == 503)
    check('rollback probe left order unchanged', before == request('http://localhost:12031', path, token=test_token()))
print('Checkpoint passed')
