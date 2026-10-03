"""Read-only real-caller comparison. Run baseline, then module and rollback."""
import argparse
import datetime
import json
import time
from pathlib import Path
from http_support import request, test_token

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ts-modulith/target/evidence'
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['baseline', 'module', 'rollback', 'final'])
args = parser.parse_args()
baseline_path = OUT / 'hybrid-baseline.json'
baseline = json.loads(baseline_path.read_text()) if args.stage != 'baseline' else None
date = baseline['date'] if baseline else (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
trip = {'startingPlace': 'Shang Hai', 'endPlace': 'Tai Yuan', 'departureTime': date}
cases = [
    ('station direct', 12345, '/api/v1/stationservice/stations', 'GET', None),
    ('station through UI', 8080, '/api/v1/stationservice/stations', 'GET', None),
    ('Basic to Station', 15680, '/api/v1/basicservice/basic/Shang%20Hai', 'GET', None),
    ('Admin Basic to Station', 18767, '/api/v1/adminbasicservice/adminbasic/stations', 'GET', None),
    ('Admin via UI to Station', 8080, '/api/v1/adminbasicservice/adminbasic/stations', 'GET', None),
    ('Travel search', 12346, '/api/v1/travelservice/trips/left', 'POST', trip),
    ('Travel2 search', 16346, '/api/v1/travel2service/trips/left', 'POST', trip),
    ('Travel search via UI', 8080, '/api/v1/travelservice/trips/left', 'POST', trip),
]
token = test_token()
# Use existing seeded orders for read-only refresh: this invokes Station name mapping.
for port, service in [(12031, 'orderservice'), (12032, 'orderOtherService')]:
    status, orders = request(f'http://127.0.0.1:{port}', f'/api/v1/{service}/order', token=token)
    if status == 200 and isinstance(orders, dict) and orders.get('data'):
        cases.append((service + ' refresh to Station', port, f'/api/v1/{service}/order/refresh', 'POST',
                      {'loginId': orders['data'][0]['accountId'], 'enableStateQuery': False,
                       'enableTravelDateQuery': False, 'enableBoughtDateQuery': False}))

results = []
for label, port, path, method, body in cases:
    start = time.perf_counter()
    try:
        status, data = request(f'http://127.0.0.1:{port}', path, method, body, token)
        # Station list order is unspecified, but every record must match.
        if 'Station' in label or label.startswith('station'):
            if isinstance(data, dict) and isinstance(data.get('data'), list) and data['data'] and isinstance(data['data'][0], dict):
                data['data'].sort(key=lambda item: item.get('id', ''))
        result = dict(label=label, http_status=status, data=data,
                      milliseconds=round((time.perf_counter() - start) * 1000, 2))
        result['healthy'] = status == 200 and (not isinstance(data, dict) or data.get('status') == 1)
    except Exception as ex:
        result = dict(label=label, healthy=False, error=str(ex))
    if baseline:
        previous = next((r for r in baseline['results'] if r['label'] == label), None)
        result['matches_baseline'] = previous is not None and all(result.get(k) == previous.get(k) for k in ['http_status', 'data', 'error'])
    results.append(result)
    print(label, 'healthy=' + str(result['healthy']), 'matches=' + str(result.get('matches_baseline', 'baseline')), flush=True)
OUT.mkdir(parents=True, exist_ok=True)
report = dict(stage=args.stage, date=date, results=results)
(OUT / f'hybrid-{args.stage}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
failed = any(not r['healthy'] or not r.get('matches_baseline', True) for r in results)
if baseline and len(results) != len(baseline['results']):
    failed = True
raise SystemExit(bool(failed))
