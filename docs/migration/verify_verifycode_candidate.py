"""Compare generated images, cookies, sessions and verify responses."""
import http.cookiejar
import json
import re
import urllib.request
from pathlib import Path
from http_support import request

root=Path(__file__).resolve().parents[2]
legacy='http://127.0.0.1:15678'
module='http://127.0.0.1:18120'
prefix='/api/v1/verifycode'
checks=[]

def check(label,passed):
    checks.append({'step':label,'passed':bool(passed)})
    print(('PASS ' if passed else 'FAIL ')+label,flush=True)
    if not passed:raise AssertionError(label)

def dimensions(data):
    if not data.startswith(b'\xff\xd8'):return None
    position=2
    while position<len(data)-9:
        if data[position]!=255:position+=1;continue
        marker=data[position+1]
        if marker in (0xC0,0xC1,0xC2,0xC3):
            return int.from_bytes(data[position+7:position+9],'big'),int.from_bytes(data[position+5:position+7],'big')
        if marker==0xD9 or marker==0xDA:break
        length=int.from_bytes(data[position+2:position+4],'big')
        position+=2+length
    return None

state=json.loads((root/'deployment/migration/.state/hybrid.json').read_text())
status,graph=request(module,'/actuator/modulith')
check('29 Spring Modulith modules',status==200 and set(graph)==set(state['modules'])|{'verifycode'})
check('Verification Code is independent',graph['verifycode']['dependencies']==[])

def probe(base,label):
    jar=http.cookiejar.CookieJar()
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with client.open(base+prefix+'/generate') as response:
        body=response.read();headers=response.headers
        check(label+' generates JPEG',response.status==200 and dimensions(body)==(60,20))
        check(label+' preserves image content type',headers.get('Content-Type') is None)
        cookies=headers.get_all('Set-Cookie') or []
        check(label+' sets captcha and session cookies',
              any(x.startswith('YsbCaptcha=') and 'Max-Age=1000' in x and
                  'Path=/' in x and 'HttpOnly' in x for x in cookies) and
              any(x.startswith('JSESSIONID=') for x in cookies))
    first=next(c.value for c in jar if c.name=='YsbCaptcha')
    check(label+' captcha cookie shape',bool(re.fullmatch('[A-F0-9]{32}',first)))
    with client.open(base+prefix+'/verify/WRONG') as response:
        check(label+' preserves verify response',response.status==200 and response.read()==b'true' and
              not any(x.startswith('YsbCaptcha=') for x in (response.headers.get_all('Set-Cookie') or [])))
    with client.open(base+prefix+'/generate') as response:response.read()
    second=next(c.value for c in jar if c.name=='YsbCaptcha')
    check(label+' rotates captcha cookie',first!=second)
    with urllib.request.urlopen(base+prefix+'/verify/WRONG') as response:
        check(label+' no-cookie verify returns true and sets cookie',
              response.status==200 and response.read()==b'true' and
              any(x.startswith('YsbCaptcha=') for x in (response.headers.get_all('Set-Cookie') or [])))

probe(legacy,'legacy')
probe(module,'module')
output=root/'ts-modulith/target/evidence/verifycode-candidate.json'
output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Verification Code candidate comparison passed')
