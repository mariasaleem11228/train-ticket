"""Compare the Avatar candidate with the live Python endpoint before routing changes."""
import base64
import hashlib
import json
import struct
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = 'http://127.0.0.1:17001/api/v1/avatar'
CANDIDATE = 'http://127.0.0.1:18140/api/v1/avatar'
PUBLIC = 'http://127.0.0.1:8080/api/v1/avatar'


def png_chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


def blank_png():
    width, height = 100, 100
    scanlines = b''.join(b'\x00' + b'\xff\xff\xff' * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
            + png_chunk(b'IDAT', zlib.compress(scanlines)) + png_chunk(b'IEND', b''))


def post(url, payload):
    request = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


face = base64.b64encode((ROOT / 'ts-avatar-service/images/test.png').read_bytes()).decode()
blank = base64.b64encode(blank_png()).decode()
results = []
for name, payload, expected in (
    ('face', {'img': face}, 200),
    ('no face', {'img': blank}, 400),
    ('missing image', {}, 400),
):
    legacy = post(LEGACY, payload)
    candidate = post(CANDIDATE, payload)
    public = post(PUBLIC, payload)
    if (legacy[0], candidate[0], public[0]) != (expected, expected, expected):
        raise AssertionError(f'{name}: unexpected statuses: {[legacy[0], candidate[0], public[0]]}')
    if name == 'face':
        if legacy[2] != candidate[2] or legacy[2] != public[2]:
            raise AssertionError(f'{name}: cropped JPEG differs')
        print('PASS face crop byte-for-byte:', hashlib.sha256(legacy[2]).hexdigest())
    elif json.loads(legacy[2])['msg'] != json.loads(candidate[2])['msg']:
        raise AssertionError(f'{name}: error response differs')
    else:
        print('PASS', name, 'status and message')
    results.append({'step': name, 'passed': True})
evidence = ROOT / 'ts-modulith/target/evidence/avatar-candidate.json'
evidence.parent.mkdir(parents=True, exist_ok=True)
evidence.write_text(json.dumps(results, indent=2))
