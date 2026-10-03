"""Manage independent module cutovers in the shared host.

prepare upgrades the host behind Station's proxy; install orders installs the next
proxy. module/legacy/restore take station or orders as a second argument. A legacy
switch disables only that module's writes and leaves the shared host running.
"""
import argparse
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from http_support import request,test_token
import station_routing as station

ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'deployment/migration/.state'
EVIDENCE=ROOT/'ts-modulith/target/evidence'
OLD_COMPOSE=['compose','-p','station-migration','-f',str(ROOT/'deployment/migration/compose.station.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.yml')]
BASE_COMPOSE=OLD_COMPOSE+['-f',str(ROOT/'deployment/migration/compose.hybrid.order-other.yml')]
COMPOSE=BASE_COMPOSE+['-f',str(ROOT/'deployment/migration/compose.spring-modulith.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.config.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.seat.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.security.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.train.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.route.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.price.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.basic.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.travel.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.travel2.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.route-plan.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.travel-plan.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.contacts.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.preserve.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.preserve-other.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.execute.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.payment.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.inside-payment.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.cancel.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.rebook.yml'),'-f',str(ROOT/'deployment/migration/compose.hybrid.assurance.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.consign-price.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.consign.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.foodmap.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.food.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.notification.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.verifycode.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.auth.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.user.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.admin-basic.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.admin-route.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.admin-travel.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.admin-order.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.admin-user.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.voucher.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.news.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.ticket-office.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.avatar.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.delivery.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.food-delivery.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.ticketinfo.yml')]
COMPOSE+=['-f',str(ROOT/'deployment/migration/compose.hybrid.wait-order.yml')]
DEFS={
 'station':dict(original='train-ticket-ts-station-service-1',proxy='station-migration-proxy',legacy='station-migration-station-legacy-1',service='station-legacy',alias='ts-station-service',port=12345,path='/api/v1/stationservice/stations',file=STATE/'routing-state.json',config=STATE/'routing'),
 'orders':dict(original='train-ticket-ts-order-service-1',proxy='orders-migration-proxy',legacy='station-migration-orders-legacy-1',service='orders-legacy',alias='ts-order-service',port=12031,path='/api/v1/orderservice/order',file=STATE/'orders-routing-state.json',config=STATE/'orders-routing'),
 'orderother':dict(original='train-ticket-ts-order-other-service-1',proxy='order-other-migration-proxy',legacy='station-migration-order-other-legacy-1',service='order-other-legacy',alias='ts-order-other-service',port=12032,path='/api/v1/orderOtherService/orderOther',file=STATE/'order-other-routing-state.json',config=STATE/'order-other-routing'),
 'config':dict(original='train-ticket-ts-config-service-1',proxy='config-migration-proxy',legacy='station-migration-config-legacy-1',service='config-legacy',alias='ts-config-service',port=15679,path='/api/v1/configservice/configs',file=STATE/'config-routing-state.json',config=STATE/'config-routing'),
 'seat':dict(original='train-ticket-ts-seat-service-1',proxy='seat-migration-proxy',legacy='station-migration-seat-legacy-1',service='seat-legacy',alias='ts-seat-service',port=18898,path='/api/v1/seatservice/welcome',file=STATE/'seat-routing-state.json',config=STATE/'seat-routing'),
 'security':dict(original='train-ticket-ts-security-service-1',proxy='security-migration-proxy',legacy='station-migration-security-legacy-1',service='security-legacy',alias='ts-security-service',port=11188,path='/api/v1/securityservice/securityConfigs',file=STATE/'security-routing-state.json',config=STATE/'security-routing'),
 'train':dict(original='train-ticket-ts-train-service-1',proxy='train-migration-proxy',legacy='station-migration-train-legacy-1',service='train-legacy',alias='ts-train-service',port=14567,path='/api/v1/trainservice/trains',file=STATE/'train-routing-state.json',config=STATE/'train-routing'),
 'route':dict(original='train-ticket-ts-route-service-1',proxy='route-migration-proxy',legacy='station-migration-route-legacy-1',service='route-legacy',alias='ts-route-service',port=11178,path='/api/v1/routeservice/routes',file=STATE/'route-routing-state.json',config=STATE/'route-routing'),
 'price':dict(original='train-ticket-ts-price-service-1',proxy='price-migration-proxy',legacy='station-migration-price-legacy-1',service='price-legacy',alias='ts-price-service',port=16579,path='/api/v1/priceservice/prices',file=STATE/'price-routing-state.json',config=STATE/'price-routing'),
 'basic':dict(original='train-ticket-ts-basic-service-1',proxy='basic-migration-proxy',legacy='station-migration-basic-legacy-1',service='basic-legacy',alias='ts-basic-service',port=15680,path='/api/v1/basicservice/welcome',file=STATE/'basic-routing-state.json',config=STATE/'basic-routing'),
 'travel':dict(original='train-ticket-ts-travel-service-1',proxy='travel-migration-proxy',legacy='station-migration-travel-legacy-1',service='travel-legacy',alias='ts-travel-service',port=12346,path='/api/v1/travelservice/welcome',file=STATE/'travel-routing-state.json',config=STATE/'travel-routing'),
 'travel2':dict(original='train-ticket-ts-travel2-service-1',proxy='travel2-migration-proxy',legacy='station-migration-travel2-legacy-1',service='travel2-legacy',alias='ts-travel2-service',port=16346,path='/api/v1/travel2service/welcome',file=STATE/'travel2-routing-state.json',config=STATE/'travel2-routing'),
 'routeplan':dict(original='train-ticket-ts-route-plan-service-1',proxy='route-plan-migration-proxy',legacy='station-migration-route-plan-legacy-1',service='route-plan-legacy',alias='ts-route-plan-service',port=14578,path='/api/v1/routeplanservice/welcome',file=STATE/'route-plan-routing-state.json',config=STATE/'route-plan-routing'),
 'travelplan':dict(original='train-ticket-ts-travel-plan-service-1',proxy='travel-plan-migration-proxy',legacy='station-migration-travel-plan-legacy-1',service='travel-plan-legacy',alias='ts-travel-plan-service',port=14322,path='/api/v1/travelplanservice/welcome',file=STATE/'travel-plan-routing-state.json',config=STATE/'travel-plan-routing'),
 'contacts':dict(original='train-ticket-ts-contacts-service-1',proxy='contacts-migration-proxy',legacy='station-migration-contacts-legacy-1',service='contacts-legacy',alias='ts-contacts-service',port=12347,path='/api/v1/contactservice/contacts',file=STATE/'contacts-routing-state.json',config=STATE/'contacts-routing'),
 'execute':dict(original='train-ticket-ts-execute-service-1',proxy='execute-migration-proxy',legacy='station-migration-execute-legacy-1',service='execute-legacy',alias='ts-execute-service',port=12386,path='/api/v1/executeservice/welcome',file=STATE/'execute-routing-state.json',config=STATE/'execute-routing'),
 'payment':dict(original='train-ticket-ts-payment-service-1',proxy='payment-migration-proxy',legacy='station-migration-payment-legacy-1',service='payment-legacy',alias='ts-payment-service',port=19001,path='/api/v1/paymentservice/welcome',file=STATE/'payment-routing-state.json',config=STATE/'payment-routing'),
 'insidepayment':dict(original='train-ticket-ts-inside-payment-service-1',proxy='inside-payment-migration-proxy',legacy='station-migration-inside-payment-legacy-1',service='inside-payment-legacy',alias='ts-inside-payment-service',port=18673,path='/api/v1/inside_pay_service/welcome',file=STATE/'inside-payment-routing-state.json',config=STATE/'inside-payment-routing'),
 'cancel':dict(original='train-ticket-ts-cancel-service-1',proxy='cancel-migration-proxy',legacy='station-migration-cancel-legacy-1',service='cancel-legacy',alias='ts-cancel-service',port=18885,path='/api/v1/cancelservice/welcome',file=STATE/'cancel-routing-state.json',config=STATE/'cancel-routing'),
 'rebook':dict(original='train-ticket-ts-rebook-service-1',proxy='rebook-migration-proxy',legacy='station-migration-rebook-legacy-1',service='rebook-legacy',alias='ts-rebook-service',port=18886,path='/api/v1/rebookservice/welcome',file=STATE/'rebook-routing-state.json',config=STATE/'rebook-routing'),
 'assurance':dict(original='train-ticket-ts-assurance-service-1',proxy='assurance-migration-proxy',legacy='station-migration-assurance-legacy-1',service='assurance-legacy',alias='ts-assurance-service',port=18888,path='/api/v1/assuranceservice/welcome',file=STATE/'assurance-routing-state.json',config=STATE/'assurance-routing'),
 'consignprice':dict(original='train-ticket-ts-consign-price-service-1',proxy='consign-price-migration-proxy',legacy='station-migration-consign-price-legacy-1',service='consign-price-legacy',alias='ts-consign-price-service',port=16110,path='/api/v1/consignpriceservice/welcome',file=STATE/'consign-price-routing-state.json',config=STATE/'consign-price-routing'),
 'consign':dict(original='train-ticket-ts-consign-service-1',proxy='consign-migration-proxy',legacy='station-migration-consign-legacy-1',service='consign-legacy',alias='ts-consign-service',port=16111,path='/api/v1/consignservice/welcome',file=STATE/'consign-routing-state.json',config=STATE/'consign-routing'),
 'foodmap':dict(original='train-ticket-ts-food-map-service-1',proxy='foodmap-migration-proxy',legacy='station-migration-foodmap-legacy-1',service='foodmap-legacy',alias='ts-food-map-service',port=18855,path='/api/v1/foodmapservice/trainfoods/welcome',file=STATE/'foodmap-routing-state.json',config=STATE/'foodmap-routing'),
 'food':dict(original='train-ticket-ts-food-service-1',proxy='food-migration-proxy',legacy='station-migration-food-legacy-1',service='food-legacy',alias='ts-food-service',port=18856,path='/api/v1/foodservice/welcome',file=STATE/'food-routing-state.json',config=STATE/'food-routing'),
 'notification':dict(original='train-ticket-ts-notification-service-1',proxy='notification-migration-proxy',legacy='station-migration-notification-legacy-1',service='notification-legacy',alias='ts-notification-service',port=17853,path='/api/v1/notifyservice/welcome',file=STATE/'notification-routing-state.json',config=STATE/'notification-routing'),
 'verifycode':dict(original='train-ticket-ts-verification-code-service-1',proxy='verifycode-migration-proxy',legacy='station-migration-verifycode-legacy-1',service='verifycode-legacy',alias='ts-verification-code-service',port=15678,path='/api/v1/verifycode/verify/WRONG',file=STATE/'verifycode-routing-state.json',config=STATE/'verifycode-routing'),
 'auth':dict(original='train-ticket-ts-auth-service-1',proxy='auth-migration-proxy',legacy='station-migration-auth-legacy-1',service='auth-legacy',alias='ts-auth-service',port=12340,path='/api/v1/auth/hello',file=STATE/'auth-routing-state.json',config=STATE/'auth-routing'),
 'user':dict(original='train-ticket-ts-user-service-1',proxy='user-migration-proxy',legacy='station-migration-user-legacy-1',service='user-legacy',alias='ts-user-service',port=12342,path='/api/v1/userservice/users/hello',file=STATE/'user-routing-state.json',config=STATE/'user-routing'),
 'adminbasic':dict(original='train-ticket-ts-admin-basic-info-service-1',proxy='admin-basic-migration-proxy',legacy='station-migration-admin-basic-legacy-1',service='admin-basic-legacy',alias='ts-admin-basic-info-service',port=18767,path='/api/v1/adminbasicservice/adminbasic/contacts',file=STATE/'admin-basic-routing-state.json',config=STATE/'admin-basic-routing'),
 'adminroute':dict(original='train-ticket-ts-admin-route-service-1',proxy='admin-route-migration-proxy',legacy='station-migration-admin-route-legacy-1',service='admin-route-legacy',alias='ts-admin-route-service',port=16113,path='/api/v1/adminrouteservice/welcome',file=STATE/'admin-route-routing-state.json',config=STATE/'admin-route-routing'),
 'admintravel':dict(original='train-ticket-ts-admin-travel-service-1',proxy='admin-travel-migration-proxy',legacy='station-migration-admin-travel-legacy-1',service='admin-travel-legacy',alias='ts-admin-travel-service',port=16114,path='/api/v1/admintravelservice/welcome',file=STATE/'admin-travel-routing-state.json',config=STATE/'admin-travel-routing'),
 'adminorder':dict(original='train-ticket-ts-admin-order-service-1',proxy='admin-order-migration-proxy',legacy='station-migration-admin-order-legacy-1',service='admin-order-legacy',alias='ts-admin-order-service',port=16112,path='/api/v1/adminorderservice/welcome',file=STATE/'admin-order-routing-state.json',config=STATE/'admin-order-routing'),
 'adminuser':dict(original='train-ticket-ts-admin-user-service-1',proxy='admin-user-migration-proxy',legacy='station-migration-admin-user-legacy-1',service='admin-user-legacy',alias='ts-admin-user-service',port=16115,path='/api/v1/adminuserservice/users/welcome',file=STATE/'admin-user-routing-state.json',config=STATE/'admin-user-routing'),
 'voucher':dict(original='train-ticket-ts-voucher-service-1',proxy='voucher-migration-proxy',legacy='station-migration-voucher-legacy-1',service='voucher-legacy',alias='ts-voucher-service',port=16101,path='/getVoucher',file=STATE/'voucher-routing-state.json',config=STATE/'voucher-routing'),
 'news':dict(original='train-ticket-ts-news-service-1',proxy='news-migration-proxy',legacy='station-migration-news-legacy-1',service='news-legacy',alias='ts-news-service',port=12862,path='/news-service/news',file=STATE/'news-routing-state.json',config=STATE/'news-routing'),
 'ticketoffice':dict(original='train-ticket-ts-ticket-office-service-1',proxy='ticket-office-migration-proxy',legacy='station-migration-ticket-office-legacy-1',service='ticket-office-legacy',alias='ts-ticket-office-service',port=16108,path='/office/',file=STATE/'ticket-office-routing-state.json',config=STATE/'ticket-office-routing'),
 'avatar':dict(original='train-ticket-ts-avatar-service-1',proxy='avatar-migration-proxy',legacy='station-migration-avatar-legacy-1',service='avatar-legacy',alias='ts-avatar-service',port=17001,path='/api/v1/avatar',file=STATE/'avatar-routing-state.json',config=STATE/'avatar-routing'),
 'preserveother':dict(original='train-ticket-ts-preserve-other-service-1',proxy='preserve-other-migration-proxy',legacy='station-migration-preserve-other-legacy-1',service='preserve-other-legacy',alias='ts-preserve-other-service',port=14569,path='/api/v1/preserveotherservice/welcome',file=STATE/'preserve-other-routing-state.json',config=STATE/'preserve-other-routing'),
 'preserve':dict(original='train-ticket-ts-preserve-service-1',proxy='preserve-migration-proxy',legacy='station-migration-preserve-legacy-1',service='preserve-legacy',alias='ts-preserve-service',port=14568,path='/api/v1/preserveservice/welcome',file=STATE/'preserve-routing-state.json',config=STATE/'preserve-routing')}

def docker(*args,env=None):
    return subprocess.check_output(['docker',*args],text=True,env=env).strip()

def inspect(name): return json.loads(docker('inspect',name))[0]

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2),encoding='utf-8')
    for attempt in range(20):
        try:
            os.replace(tmp,path)
            return
        except PermissionError:
            if attempt == 19: raise
            time.sleep(0.1)

def owner(module,mode):
    path=STATE/'ownership/ownership.json'
    values=json.loads(path.read_text()) if path.exists() else {}
    values[module]=mode;write_json(path,values)

def configure(module,mode,reload=True):
    definition=DEFS[module];directory=definition['config'];directory.mkdir(parents=True,exist_ok=True)
    header={'orderother':'OrderOther','routeplan':'RoutePlan','travelplan':'TravelPlan','preserveother':'PreserveOther','insidepayment':'InsidePayment','consignprice':'ConsignPrice','foodmap':'FoodMap','verifycode':'VerifyCode','adminbasic':'AdminBasic','adminroute':'AdminRoute','admintravel':'AdminTravel','adminorder':'AdminOrder','adminuser':'AdminUser','ticketoffice':'TicketOffice'}.get(module,module.title())
    if mode=='maintenance': location='return 503;'
    else:
        target='ts-modulith:18080' if mode=='module' else f"{definition['service']}:{definition['port']}"
        location=f'''resolver 127.0.0.11 valid=5s ipv6=off;
        set $backend http://{target}; proxy_pass $backend$request_uri;
        proxy_set_header Host $host; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1; proxy_set_header Connection "";
        proxy_connect_timeout 5s; proxy_read_timeout 30s;'''
    (directory/'default.conf').write_text(f'''server {{ listen {definition['port']};
      add_header X-{header}-Backend "{mode}" always;
      location / {{ {location} }}
    }}
''',encoding='utf-8')
    if reload:
        docker('exec',definition['proxy'],'nginx','-t')
        docker('exec',definition['proxy'],'nginx','-s','reload')
        time.sleep(2)

def ready(module,backend):
    definition=DEFS[module]
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        try:
            ip=next(iter(inspect(backend)['NetworkSettings']['Networks'].values()))['IPAddress']
            port=18080 if backend==station.MODULE else definition['port']
            if module in ('voucher','avatar'):
                docker('exec',definition['proxy'],'nc','-z','-w','2',ip,str(port))
                return
            wget=['wget','-qO-']
            if module in ('security','contacts','preserve','preserveother','execute','payment','insidepayment','cancel','rebook','assurance','consignprice','consign','adminroute','admintravel','adminorder','adminuser'):wget+=['--header','Authorization: Bearer '+test_token('ROLE_USER' if module=='assurance' else 'ROLE_ADMIN')]
            body=docker('exec',definition['proxy'],*wget,f"http://{ip}:{port}{definition['path']}")
            if (module=='ticketoffice' and body=='welcome to ts-ticket-office-service') or \
                    (module=='news' and 'News Service Complete' in body) or \
                    (module in ('seat','basic','travel') and 'Welcome to [ '+module.title()+' Service ] !' in body) or \
                    (module=='travel2' and 'Welcome to [ Travle2 Service ] !' in body) or \
                    (module=='routeplan' and 'Welcome to [ RoutePlan Service ] !' in body) or \
                    (module=='travelplan' and 'Welcome to [ TravelPlan Service ] !' in body) or \
                    (module=='preserve' and 'Welcome to [ Preserve Service ] !' in body) or \
                    (module=='preserveother' and 'Welcome to [ PreserveOther Service ] !' in body) or \
                    (module=='execute' and 'Welcome to [ Execute Service ] !' in body) or \
                    (module=='payment' and 'Welcome to [ Payment Service ] !' in body) or \
                    (module=='insidepayment' and 'Welcome to [ InsidePayment Service ] !' in body) or \
                    (module=='cancel' and 'Welcome to [ Cancel Service ] !' in body) or \
                    (module=='rebook' and 'Welcome to [ Rebook Service ] !' in body) or \
                    (module=='assurance' and 'Welcome to [ Assurance Service ] !' in body) or \
                    (module=='consignprice' and 'Welcome to [ ConsignPrice Service ] !' in body) or \
                    (module=='consign' and 'Welcome to [ Consign Service ] !' in body) or \
                    (module=='foodmap' and 'Welcome to [ Train Food Service ] !' in body) or \
                    (module=='food' and 'Welcome to [ Food Service ] !' in body) or \
                    (module=='notification' and 'Welcome to [ Notification Service ] !' in body) or \
                    (module=='verifycode' and body=='true') or \
                    (module=='auth' and body=='hello') or \
                    (module=='user' and body=='Hello') or \
                    (module=='adminroute' and 'Welcome to [ AdminRoute Service ] !' in body) or \
                    (module=='admintravel' and 'Welcome to [ AdminTravel Service ] !' in body) or \
                    (module=='adminorder' and 'Welcome to [Admin Order Service] !' in body) or \
                    (module=='adminuser' and 'Welcome to [ AdminUser Service ] !' in body) or \
                    (module not in ('news','ticketoffice','seat','basic','travel','travel2','routeplan','travelplan','preserve','preserveother','execute','payment','insidepayment','cancel','rebook','assurance','consignprice','consign','foodmap','food','notification','verifycode','auth','user','adminroute','admintravel','adminorder','adminuser') and json.loads(body).get('status')==1):return
        except (subprocess.CalledProcessError,ValueError,KeyError):pass
        print('Waiting for',backend,flush=True);time.sleep(3)
    raise RuntimeError('Backend readiness deadline: '+backend)

def require_gate(filename,min_count):
    results=json.loads((EVIDENCE/filename).read_text(encoding='utf-8'))
    if len(results)<min_count or not all(r['passed'] for r in results):raise RuntimeError('Failed gate: '+filename)

def prepare():
    require_gate('station-contracts.json',32)
    require_gate('orders-contracts.json',33)
    require_gate('booking-baseline.json',15)
    state=json.loads(DEFS['station']['file'].read_text())
    if state['mode']!='module':raise RuntimeError('Station must be serving from its module first.')
    if (STATE/'hybrid.json').exists():raise RuntimeError('Host already prepared; use per-module switches.')
    configure('station','maintenance')
    owner('station','maintenance');owner('orders','legacy')
    try:
        docker(*OLD_COMPOSE,'up','-d','modulith')
        ready('station',station.MODULE)
        owner('station','module');configure('station','module')
        write_json(STATE/'hybrid.json',{'stage':'orders','image':inspect(station.MODULE)['Image'],'modules':['station','orders']})
    except Exception:
        # Return to the previous Station-only image if the shared host upgrade fails.
        owner('station','module')
        docker(*station.COMPOSE,'up','-d','modulith',env=dict(os.environ,STATION_WRITES_ENABLED='true'))
        ready('station',station.MODULE);configure('station','module')
        raise

def prepare_order_other():
    require_gate('order-other-contracts.json',31)
    if not (EVIDENCE/'order-other-backup.archive').exists():raise RuntimeError('OrderOther backup required')
    for name in ('station','orders'):
        if json.loads(DEFS[name]['file'].read_text())['mode']!='module':
            raise RuntimeError(name+' must be serving from the module')
    state=json.loads((STATE/'hybrid.json').read_text())
    if 'orderother' in state['modules']:raise RuntimeError('OrderOther already prepared')
    owner('orderother','legacy')
    for name in ('station','orders'):configure(name,'maintenance');owner(name,'maintenance')
    try:
        docker(*COMPOSE,'up','-d','modulith')
        for name in ('station','orders'):ready(name,station.MODULE)
        status,response=request('http://127.0.0.1:18080',DEFS['orderother']['path'],token=test_token())
        if status!=200 or response.get('status')!=1:raise RuntimeError('OrderOther module failed readiness')
        for name in ('station','orders'):owner(name,'module');configure(name,'module')
        state.update(stage='orderother',image=inspect(station.MODULE)['Image'],modules=['station','orders','orderother'])
        write_json(STATE/'hybrid.json',state)
    except Exception:
        docker(*OLD_COMPOSE,'up','-d','modulith')
        for name in ('station','orders'):
            ready(name,station.MODULE);owner(name,'module');configure(name,'module')
        raise

def install(module):
    if module not in ('orders','orderother','config','seat','security','train','route','price','basic','travel','travel2','routeplan','travelplan','contacts','preserve','preserveother','execute','payment','insidepayment','cancel','rebook','assurance','consignprice','consign','foodmap','food','notification','verifycode','auth','user','adminbasic','adminroute','admintravel','adminorder','adminuser','voucher','news','ticketoffice','avatar'):raise RuntimeError('Station proxy is already installed.')
    if not (STATE/'hybrid.json').exists():raise RuntimeError('Prepare shared host first.')
    filename={'orders':'orders-contracts.json','orderother':'order-other-contracts.json','config':'config-comparison.json','seat':'seat-candidate.json','security':'security-comparison.json','train':'train-comparison.json','route':'route-comparison.json','price':'price-comparison.json','basic':'basic-comparison.json','travel':'travel-comparison.json','travel2':'travel2-comparison.json','routeplan':'route-plan-comparison.json','travelplan':'travel-plan-comparison.json','contacts':'contacts-comparison.json','preserve':'preserve-candidate.json','preserveother':'preserve-other-candidate.json','execute':'execute-candidate.json','payment':'payment-candidate.json','insidepayment':'inside-payment-candidate.json','cancel':'cancel-candidate.json','rebook':'rebook-candidate.json','assurance':'assurance-candidate.json','consignprice':'consign-price-candidate.json','consign':'consign-candidate.json','foodmap':'foodmap-candidate.json','food':'food-candidate.json','notification':'notification-candidate.json','verifycode':'verifycode-candidate.json','auth':'auth-candidate.json','user':'user-candidate.json','adminbasic':'admin-basic-candidate.json','adminroute':'admin-route-candidate.json','admintravel':'admin-travel-candidate.json','adminorder':'admin-order-candidate.json','adminuser':'admin-user-candidate.json','voucher':'voucher-candidate.json','news':'news-candidate.json','ticketoffice':'ticket-office-candidate.json','avatar':'avatar-candidate.json'}[module]
    archive={'orders':'orders-backup.archive','orderother':'order-other-backup.archive','config':'config-backup.archive','seat':None,'security':'security-backup.archive','train':None,'route':None,'price':None,'basic':None,'travel':None,'travel2':None,'routeplan':None,'travelplan':None,'contacts':None,'preserve':None,'preserveother':None,'execute':None,'payment':None,'insidepayment':None,'cancel':None,'rebook':None,'assurance':None,'consignprice':None,'consign':None,'foodmap':None,'food':None,'notification':None,'verifycode':None,'auth':None,'user':None,'adminbasic':None,'adminroute':None,'admintravel':None,'adminorder':None,'adminuser':None,'voucher':None,'news':None,'ticketoffice':None,'avatar':None}[module]
    require_gate(filename,{'orders':33,'orderother':31,'config':20,'seat':17,'security':15,'train':22,'route':30,'price':26,'basic':26,'travel':42,'travel2':42,'routeplan':22,'travelplan':26,'contacts':11,'preserve':7,'preserveother':7,'execute':22,'payment':15,'insidepayment':51,'cancel':73,'rebook':74,'assurance':16,'consignprice':16,'consign':20,'foodmap':15,'food':20,'notification':18,'verifycode':16,'auth':22,'user':17,'adminbasic':12,'adminroute':15,'admintravel':20,'adminorder':19,'adminuser':18,'voucher':10,'news':6,'ticketoffice':17,'avatar':3}[module])
    if module=='foodmap' and any(not (STATE/'backups'/name).exists() for name in ('foodmap-stores.archive','foodmap-trainfoods.archive')):
        raise RuntimeError('Food Map collection backups required')
    if module=='food' and not (STATE/'backups/food.archive').exists():raise RuntimeError('Food orders backup required')
    if module=='notification' and not (STATE/'backups/notification.archive').exists():raise RuntimeError('Notification Mongo backup required')
    if module=='voucher' and not (STATE/'backups/voucher.sql').exists():raise RuntimeError('Voucher MySQL backup required')
    if module=='ticketoffice' and not (STATE/'backups/ticket-office.archive').exists():raise RuntimeError('Ticket Office Mongo backup required')
    if module=='auth' and not (STATE/'backups/auth.archive').exists():raise RuntimeError('Auth Mongo backup required')
    if module=='user' and any(not (STATE/'backups'/name).exists() for name in ('user-cutover-user.archive','user-cutover-auth.archive')):raise RuntimeError('User and Auth Mongo backups required')
    if module=='consign' and not (STATE/'backups/consign.archive').exists():raise RuntimeError('Consign backup required')
    if module=='consignprice' and not (STATE/'backups/consign-price.archive').exists():raise RuntimeError('ConsignPrice backup required')
    if module=='assurance' and not (STATE/'backups/assurance.archive').exists():raise RuntimeError('Assurance collection backup required')
    if module=='rebook' and any(not (STATE/'backups'/item).exists() for item in ('rebook-orders.archive','rebook-order-other.archive','rebook-wallet-payment.archive')):
        raise RuntimeError('Rebook dependency backups required')
    if module=='cancel' and any(not (STATE/'backups'/item).exists() for item in ('cancel-orders.archive','cancel-order-other.archive','cancel-wallet-add-money.archive')):
        raise RuntimeError('Cancel dependency backups required')
    if module=='insidepayment' and any(not (STATE/'backups'/item).exists() for item in ('inside-payment-payment.archive','inside-payment-addMoney.archive')):
        raise RuntimeError('Inside Payment collection backups required')
    if module=='payment' and any(not (STATE/'backups'/item).exists() for item in ('payment.archive','payment-add-money.archive')):
        raise RuntimeError('Payment collection backups required')
    if module in ('train','route','price','travel','travel2','contacts') and not (STATE/f'backups/{module}.archive').exists():raise RuntimeError(module+' backup required')
    if module=='preserve':
        if not (STATE/'backups/preserve-orders.archive').exists():raise RuntimeError('Preserve Orders backup required')
        require_gate('booking-preserve-baseline.json',15)
    if module=='preserveother':
        if not (STATE/'backups/preserve-other-orders.archive').exists():raise RuntimeError('PreserveOther OrderOther backup required')
        require_gate('booking-other-preserve-other-baseline.json',15)
    if module=='execute':
        if not (STATE/'backups/execute-orders.archive').exists() or not (STATE/'backups/execute-order-other.archive').exists():raise RuntimeError('Execute order backups required')
    if module=='contacts':require_gate('contacts-write-comparison.json',12)
    if archive and not (EVIDENCE/archive).exists():raise RuntimeError(module+' backup required')
    d=DEFS[module]
    if d['file'].exists() and json.loads(d['file'].read_text())['mode']!='restored':raise RuntimeError('Already installed')
    original=inspect(d['original']);networks=original['NetworkSettings']['Networks']
    if len(networks)!=1:raise RuntimeError('Expected one original network')
    network,net=next(iter(networks.items()))
    state=dict(original=d['original'],network=network,ip=net['IPAddress'],image=original['Image'],mode='installing',restart_policy=original['HostConfig']['RestartPolicy']['Name'])
    write_json(d['file'],state)
    owner(module,'legacy')
    try:
        configure(module,'maintenance',reload=False)
        docker('update','--restart=no',d['original']);docker('stop','-t','30',d['original'])
        docker('network','disconnect',network,d['original'])
        docker('run','-d','--name',d['proxy'],'--restart','unless-stopped','--network',network,'--ip',state['ip'],
               '--network-alias',d['alias'],'-p',f"{d['port']}:{d['port']}",
               '--mount',f"type=bind,source={d['config']},target=/etc/nginx/conf.d,readonly",
               'nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10')
        docker(*COMPOSE,'--profile','routing','up','-d',d['service'])
        ready(module,d['legacy']);configure(module,'legacy')
        state['mode']='legacy';write_json(d['file'],state)
    except Exception:
        if module=='ticketoffice':
            # The original Node image reseeds Mongo on startup. Leave the proxy
            # in maintenance for inspection instead of restarting that image.
            raise
        restore(module);raise

def switch(module,mode):
    d=DEFS[module];state=json.loads(d['file'].read_text())
    if state['mode']=='restored':raise RuntimeError('Install this proxy first')
    configure(module,'maintenance');owner(module,'maintenance')
    state['mode']='maintenance';write_json(d['file'],state)
    try:
        # Wait out active application requests before handing write ownership over.
        time.sleep(3)
        if mode=='module':
            docker('stop','-t','30',d['legacy']);ready(module,station.MODULE)
        else:
            docker(*COMPOSE,'--profile','routing','up','-d',d['service']);ready(module,d['legacy'])
        owner(module,mode);configure(module,mode)
        state['mode']=mode;write_json(d['file'],state)
    except Exception:
        if module=='ticketoffice':
            # The no-reseed clone is the only safe fallback after module writes.
            docker(*COMPOSE,'--profile','routing','up','-d',d['service'])
            ready(module,d['legacy'])
            owner(module,'legacy');configure(module,'legacy')
            state['mode']='legacy';write_json(d['file'],state)
            raise
        restore(module);raise

def restore(module):
    if module=='ticketoffice':
        raise RuntimeError('Direct original restore would reseed and erase Ticket Office writes; switch to the no-reseed legacy backend instead')
    d=DEFS[module];state=json.loads(d['file'].read_text())
    owner(module,'legacy')
    names=docker('ps','-a','--format','{{.Names}}').splitlines()
    if d['proxy'] in names:docker('stop','-t','30',d['proxy']);docker('rm',d['proxy'])
    if d['legacy'] in names:docker('stop','-t','30',d['legacy'])
    if state['network'] not in inspect(d['original'])['NetworkSettings']['Networks']:
        docker('network','connect','--ip',state['ip'],'--alias',d['alias'],state['network'],d['original'])
    docker('update','--restart='+state.get('restart_policy','always'),d['original']);docker('start',d['original'])
    from http_support import wait_ready
    if module in ('security','contacts','preserve','preserveother','execute','payment','insidepayment','cancel','rebook','assurance','consignprice','consign','adminroute','admintravel','adminorder','adminuser'):
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            try:
                status,body=request('http://127.0.0.1:'+str(d['port']),d['path'],token=test_token('ROLE_USER' if module=='assurance' else 'ROLE_ADMIN'))
                expected_welcome={'preserve':'Welcome to [ Preserve Service ] !',
                                  'preserveother':'Welcome to [ PreserveOther Service ] !',
                                  'execute':'Welcome to [ Execute Service ] !',
                                  'payment':'Welcome to [ Payment Service ] !',
                                  'insidepayment':'Welcome to [ InsidePayment Service ] !',
                                  'cancel':'Welcome to [ Cancel Service ] !',
                                  'rebook':'Welcome to [ Rebook Service ] !',
                                  'assurance':'Welcome to [ Assurance Service ] !'}
                expected_welcome['consignprice']='Welcome to [ ConsignPrice Service ] !'
                expected_welcome['consign']='Welcome to [ Consign Service ] !'
                expected_welcome['adminroute']='Welcome to [ AdminRoute Service ] !'
                expected_welcome['admintravel']='Welcome to [ AdminTravel Service ] !'
                expected_welcome['adminorder']='Welcome to [Admin Order Service] !'
                expected_welcome['adminuser']='Welcome to [ AdminUser Service ] !'
                valid=body==expected_welcome[module] if module in expected_welcome else body.get('status')==1
                if status==200 and valid:break
            except OSError:pass
            time.sleep(3)
        else:raise RuntimeError('Restored protected backend not ready')
    elif module in ('voucher','avatar'):
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            try:
                with socket.create_connection(('127.0.0.1',d['port']),timeout=2):break
            except OSError:time.sleep(3)
        else:raise RuntimeError('Restored Voucher backend not ready')
    else:wait_ready('http://127.0.0.1:'+str(d['port']),d['path'])
    state['mode']='restored';write_json(d['file'],state)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','prepare-order-other','install','module','legacy','restore','status'])
    parser.add_argument('service',nargs='?',choices=list(DEFS))
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='prepare-order-other':prepare_order_other()
    elif args.action=='status':
        for name,d in DEFS.items():
            if d['file'].exists():print(name,d['file'].read_text())
    elif args.service is None:parser.error('Service required')
    elif args.action=='install':install(args.service)
    elif args.action=='restore':restore(args.service)
    else:switch(args.service,args.action)
