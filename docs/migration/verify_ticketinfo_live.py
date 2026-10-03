"""Compare live TicketInfo module responses with the retained legacy container."""
import json
import urllib.request

path='/api/v1/ticketinfoservice'


def call(port,method,suffix,body=None):
    request=urllib.request.Request(f'http://127.0.0.1:{port}{suffix}',
        data=None if body is None else json.dumps(body).encode(),method=method,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=25) as response:
        raw=response.read().decode()
        return response.status,json.loads(raw) if raw.startswith('{') else raw


with urllib.request.urlopen('http://127.0.0.1:18080/actuator/modulith',timeout=15) as response:
    graph=json.load(response)
assert len(graph)>=43 and {d['target'] for d in graph['ticketinfo']['dependencies']}=={'basic','station'}
for endpoint in ('/welcome','/ticketinfo/Shang%20Hai','/ticketinfo/NoSuchStation'):
    assert call(15681,'GET',path+endpoint)==call(18080,'GET',path+endpoint),endpoint
body={'trip':{'tripId':{'type':'D','number':'1345'},'trainTypeId':'DongCheOne',
              'routeId':'f3d4d4ef-693b-4456-8eed-59c0d717dd08'},
      'startingPlace':'Shang Hai','endPlace':'Su Zhou','departureTime':1790985600000}
assert call(15681,'POST',path+'/ticketinfo',body)==call(18080,'POST',path+'/ticketinfo',body)
print('PASS TicketInfo live module matches legacy GET and POST contracts')
