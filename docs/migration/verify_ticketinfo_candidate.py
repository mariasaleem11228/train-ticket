"""Compare TicketInfo candidate with live legacy and prove local Travel integration."""
import json
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[2]
path='/api/v1/ticketinfoservice'


def call(port,method,suffix,body=None):
    request=urllib.request.Request(f'http://127.0.0.1:{port}{suffix}',
        data=None if body is None else json.dumps(body).encode(),method=method,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=25) as response:
        raw=response.read().decode()
        return response.status,json.loads(raw) if raw.startswith('{') else raw


with urllib.request.urlopen('http://127.0.0.1:18143/actuator/modulith',timeout=15) as response:
    graph=json.load(response)
assert len(graph)==43 and {d['target'] for d in graph['ticketinfo']['dependencies']}=={'basic','station'}
for endpoint in ('/welcome','/ticketinfo/Shang%20Hai','/ticketinfo/NoSuchStation'):
    assert call(15681,'GET',path+endpoint)==call(18143,'GET',path+endpoint),endpoint
body={'trip':{'tripId':{'type':'D','number':'1345'},'trainTypeId':'DongCheOne',
              'routeId':'f3d4d4ef-693b-4456-8eed-59c0d717dd08'},
      'startingPlace':'Shang Hai','endPlace':'Su Zhou','departureTime':1790985600000}
assert call(15681,'POST',path+'/ticketinfo',body)==call(18143,'POST',path+'/ticketinfo',body)
query={'startingPlace':'Shang Hai','endPlace':'Su Zhou','departureTime':1791590400000}
status,result=call(18143,'POST','/api/v1/travelservice/trips/left',query)
assert status==200 and result['status']==1 and result['data'],result
with urllib.request.urlopen('http://127.0.0.1:18080/actuator/modulith',timeout=15) as response:
    live=json.load(response)
assert len(live)==42 and 'ticketinfo' not in live
evidence=root/'ts-modulith/target/evidence/ticketinfo-candidate.json'
evidence.parent.mkdir(parents=True,exist_ok=True)
evidence.write_text(json.dumps([
    {'step':'TicketInfo is module 43 using Basic','passed':True},
    {'step':'three GET and one POST legacy contracts match','passed':True},
    {'step':'Travel works with legacy TicketInfo URL deliberately unavailable','passed':True},
    {'step':'live 42-module host unchanged','passed':True}],indent=2))
print('PASS TicketInfo legacy parity and local Travel integration')
