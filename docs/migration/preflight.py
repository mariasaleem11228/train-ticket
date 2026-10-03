"""Read-only inventory of the active legacy stack; no environment values recorded."""
import concurrent.futures
import datetime
import json
import subprocess
import urllib.request
from pathlib import Path
from http_support import test_token

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ts-modulith/target/evidence'
OUT.mkdir(parents=True, exist_ok=True)
ids = subprocess.check_output(['docker', 'ps', '-aq'], text=True).split()
containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True))

def check(container):
    result = dict(name=container['Name'].lstrip('/'), image=container['Config']['Image'],
                  image_id=container['Image'], state=container['State']['Status'],
                  restarts=container['RestartCount'])
    ports = container['NetworkSettings'].get('Ports') or {}
    result['ports'] = {port: values for port, values in ports.items() if values}
    if result['state'] == 'running' and 'codewisdom/' in result['image']:
        java = any('java' in arg for arg in (container['Config'].get('Entrypoint') or []) + (container['Config'].get('Cmd') or []))
        for port, bindings in result['ports'].items():
            host_port = bindings[0]['HostPort']
            url = 'http://127.0.0.1:' + host_port + ('/health' if java else '/')
            try:
                req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + test_token()})
                with urllib.request.urlopen(req, timeout=15) as response:
                    body = response.read().decode()
                    result['probe'] = {'url': url, 'http_status': response.status,
                                       'body': body[:200] if java else '(body omitted)'}
            except Exception as ex:
                result['probe'] = {'url': url, 'error': str(ex)}
            break
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(check, containers))
report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'containers': results}
(OUT / 'preflight.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
for result in results:
    if result.get('probe'):
        print(result['name'], result['probe'])
print('Full inventory:', OUT / 'preflight.json')
