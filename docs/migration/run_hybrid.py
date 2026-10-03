"""Start the existing hybrid stack and its optional side-by-side comparison services.

This resumes existing legacy containers, retaining their IPs and data. It does not
recreate the old Compose stack or start originals whose identities belong to proxies.
"""
import argparse
import json
import subprocess
from pathlib import Path
import hybrid_routing as routing
import recover_proxy_ips

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--comparisons',action='store_true',help='Also start isolated legacy/module test endpoints')
parser.add_argument('--price-comparison',action='store_true',help='Start only the isolated Price endpoints to save memory')
parser.add_argument('--basic-comparison',action='store_true',help='Start the read-only Basic candidate')
parser.add_argument('--travel-comparison',action='store_true',help='Start only Travel comparison endpoints')
parser.add_argument('--travel2-comparison',action='store_true',help='Start only Travel2 comparison endpoints')
args=parser.parse_args()
if not (routing.STATE/'hybrid.json').exists():raise SystemExit('Complete stage-02 prepare/install before using this launcher.')
states={name:json.loads(d['file'].read_text()) for name,d in routing.DEFS.items() if d['file'].exists()}
excluded={s['original'] for s in states.values() if s['mode']!='restored'}
recover_proxy_ips.recover()
ids=routing.docker('ps','-aq').split()
containers=json.loads(routing.docker('inspect',*ids))
# Start fixed-IP compatibility proxies before dynamic-IP services. After a Docker
# restart, a previously stopped proxy's address may have been leased elsewhere.
for name,state in states.items():
    if state['mode']=='restored':continue
    d=routing.DEFS[name]
    if routing.inspect(d['proxy'])['State']['Running']:continue
    # Docker may auto-start another container while this loop is running.
    running_ids=routing.docker('ps','-q').split()
    current=json.loads(routing.docker('inspect',*running_ids)) if running_ids else []
    occupants=[c['Name'].lstrip('/') for c in current if c['State']['Running'] and
               c['Name'].lstrip('/')!=d['proxy'] and
               any(net.get('IPAddress')==state['ip'] for net in c['NetworkSettings']['Networks'].values())]
    if occupants:
        occupant=occupants[0]
        if occupant in excluded or occupant in (item['proxy'] for item in routing.DEFS.values()):
            raise SystemExit('Reserved proxy IP is held by another migration component: '+occupant)
        routing.docker('stop',occupant)
        try:routing.docker('start',d['proxy'])
        finally:routing.docker('start',occupant)
        print('Reassigned reserved proxy IP from',occupant,'to',d['proxy'],flush=True)
    else:routing.docker('start',d['proxy'])
legacy=[c for c in containers if c['Config'].get('Labels',{}).get('com.docker.compose.project')=='train-ticket'
        and c['Name'].lstrip('/') not in excluded and c['State']['Status'] in ('created','exited')]
# Start databases before callers. No container is removed/recreated here.
legacy.sort(key=lambda c:0 if any(x in c['Config']['Image'] for x in ['mongo','mysql','redis']) else 1)
for c in legacy:
    routing.docker('start',c['Id']);print('Started',c['Name'].lstrip('/'),flush=True)
routing.docker('compose','-p','migration-infra','-f',str(ROOT/'deployment/migration/compose.infrastructure.yml'),'up','-d')
if 'delivery' in json.loads((routing.STATE/'hybrid.json').read_text())['modules']:
    routing.docker(*routing.COMPOSE,'up','-d','delivery-mysql')
if 'fooddelivery' in json.loads((routing.STATE/'hybrid.json').read_text())['modules']:
    routing.docker(*routing.COMPOSE,'up','-d','food-delivery-mysql')
if 'waitorder' in json.loads((routing.STATE/'hybrid.json').read_text())['modules']:
    routing.docker(*routing.COMPOSE,'up','-d','wait-order-mysql')
routing.docker(*routing.COMPOSE,'up','-d','modulith')
for name,state in states.items():
    if state['mode']=='restored':continue
    if state['mode'] not in ('module','legacy'):raise SystemExit('Unfinished cutover: inspect '+name)
    d=routing.DEFS[name]
    if state['mode']=='legacy':routing.docker(*routing.COMPOSE,'--profile','routing','up','-d',d['service'])
    routing.ready(name,routing.station.MODULE if state['mode']=='module' else d['legacy'])
if args.comparisons:
    comparison=routing.station.COMPOSE+['-f',str(ROOT/'deployment/migration/compose.orders.yml'),'-f',str(ROOT/'deployment/migration/compose.order-other.yml'),'-f',str(ROOT/'deployment/migration/compose.config.yml'),'-f',str(ROOT/'deployment/migration/compose.seat.yml'),'-f',str(ROOT/'deployment/migration/compose.security.yml'),'-f',str(ROOT/'deployment/migration/compose.train.yml'),'-f',str(ROOT/'deployment/migration/compose.route.yml'),'-f',str(ROOT/'deployment/migration/compose.price.yml')]
    routing.docker(*comparison,'up','-d','station-test-mongo','station-legacy-test','orders-legacy-test','order-other-legacy-test','config-legacy-test','config-candidate','seat-legacy-test','security-legacy-test','security-candidate','train-legacy-test','train-candidate','route-legacy-test','route-candidate','price-legacy-test','price-candidate')
    from http_support import wait_ready
    for service,port,path in [('station-module-test',18081,'/api/v1/stationservice/stations'),
                              ('orders-module-test',18082,'/api/v1/orderservice/order'),
                              ('order-other-module-test',18084,'/api/v1/orderOtherService/orderOther'),
                              ('config-module-test',18087,'/actuator/health'),
                              ('seat-candidate',18088,'/api/v1/seatservice/welcome'),
                              ('security-module-test',18090,'/actuator/health'),
                              ('security-candidate',18089,'/actuator/health'),
                              ('train-module-test',18092,'/actuator/health'),
                              ('train-candidate',18091,'/actuator/health'),
                              ('route-module-test',18094,'/actuator/health'),
                              ('route-candidate',18093,'/actuator/health'),
                              ('price-module-test',18096,'/actuator/health'),
                              ('price-candidate',18095,'/actuator/health')]:
        routing.docker(*comparison,'up','-d',service)
        wait_ready('http://127.0.0.1:'+str(port),path,seconds=300)
if args.price_comparison and not args.comparisons:
    comparison=routing.station.COMPOSE+['-f',str(ROOT/'deployment/migration/compose.price.yml')]
    routing.docker(*comparison,'up','-d','station-test-mongo','price-legacy-test','price-module-test','price-candidate')
    from http_support import wait_ready
    for port,path in [(26579,'/api/v1/priceservice/prices/welcome'),
                      (18096,'/actuator/health'),(18095,'/actuator/health')]:
        wait_ready('http://127.0.0.1:'+str(port),path,seconds=300)
if args.basic_comparison:
    comparison=routing.station.COMPOSE+['-f',str(ROOT/'deployment/migration/compose.basic.yml')]
    routing.docker(*comparison,'up','-d','basic-candidate')
    from http_support import wait_ready
    wait_ready('http://127.0.0.1:18097','/actuator/health',seconds=300)
if args.travel_comparison:
    comparison=routing.station.COMPOSE+['-f',str(ROOT/'deployment/migration/compose.travel.yml')]
    routing.docker(*comparison,'up','-d','station-test-mongo','travel-legacy-test','travel-module-test','travel-candidate')
    from http_support import wait_ready
    for port,path in [(22346,'/api/v1/travelservice/welcome'),
                      (18099,'/actuator/health'),(18098,'/actuator/health')]:
        wait_ready('http://127.0.0.1:'+str(port),path,seconds=300)
if args.travel2_comparison:
    comparison=routing.station.COMPOSE+['-f',str(ROOT/'deployment/migration/compose.travel2.yml')]
    routing.docker(*comparison,'up','-d','station-test-mongo','travel2-legacy-test','travel2-module-test','travel2-candidate')
    from http_support import wait_ready
    for port,path in [(26346,'/api/v1/travel2service/welcome'),
                      (18101,'/actuator/health'),(18100,'/actuator/health')]:
        wait_ready('http://127.0.0.1:'+str(port),path,seconds=300)
# The deployed UI uses fixed upstream hostnames. NGINX resolves their Docker IPs
# when it starts, so refresh those addresses after all services have been resumed.
if 'rebook' in json.loads((routing.STATE/'hybrid.json').read_text())['modules']:
    ui='train-ticket-ts-ui-dashboard-1'
    if routing.inspect(ui)['Config']['Image']!='train-ticket/ts-ui-dashboard:rebook-fix':
        routing.docker('compose','-p','train-ticket',
                       '-f',str(ROOT/'docker-compose.yml'),
                       '-f',str(ROOT/'deployment/migration/compose.ui-rebook.yml'),
                       'up','-d','--no-deps','ts-ui-dashboard')
routing.docker('exec','train-ticket-ts-ui-dashboard-1','nginx','-t')
routing.docker('exec','train-ticket-ts-ui-dashboard-1','nginx','-s','reload')
print('Hybrid UI: http://localhost:8080')
print('Local email sink: http://localhost:8025')
if args.comparisons:print('Isolated Orders: legacy http://localhost:22031 ; module http://localhost:18082')
if args.comparisons:print('Isolated OrderOther: legacy http://localhost:22032 ; module http://localhost:18084')
if args.comparisons:print('Isolated Config: legacy http://localhost:25679 ; module http://localhost:18087')
if args.comparisons:print('Seat comparison: legacy http://localhost:28898 ; module http://localhost:18088')
if args.comparisons:print('Security comparison: legacy http://localhost:21188 ; module http://localhost:18090')
if args.comparisons:print('Train comparison: legacy http://localhost:24567 ; module http://localhost:18092')
if args.comparisons:print('Route comparison: legacy http://localhost:21178 ; module http://localhost:18094')
if args.comparisons:print('Price comparison: legacy http://localhost:26579 ; module http://localhost:18096')
if args.price_comparison:print('Price comparison: legacy http://localhost:26579 ; module http://localhost:18096')
if args.basic_comparison:print('Basic comparison: legacy http://localhost:15680 ; module http://localhost:18097')
if args.travel_comparison:print('Travel comparison: legacy http://localhost:22346 ; module http://localhost:18099')
if args.travel2_comparison:print('Travel2 comparison: legacy http://localhost:26346 ; module http://localhost:18101')
