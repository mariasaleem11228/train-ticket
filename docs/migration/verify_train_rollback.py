"""Prove Train's old service can read and update module-created data after rollback."""
import uuid
from http_support import request
import hybrid_routing as routing

base = 'http://127.0.0.1:14567'
module = 'http://127.0.0.1:18080'
path = '/api/v1/trainservice/trains'
name = 'migration-train-rollback-' + uuid.uuid4().hex
initial = {'id': name, 'economyClass': 22, 'confortClass': 11, 'averageSpeed': 180}
changed = {**initial, 'averageSpeed': 200}

def call(host, suffix='', method='GET', body=None):
    return request(host, path + suffix, method, body)

try:
    status, result = call(base, method='POST', body=initial)
    assert status == 200 and result['status'] == 1
    assert call(base, '/' + name)[1]['data'] == initial
    routing.switch('train', 'legacy')
    assert call(base, '/' + name)[1]['data'] == initial
    assert call(module, method='PUT', body=changed)[0] == 503
    status, result = call(base, method='PUT', body=changed)
    assert status == 200 and result['status'] == 1
    assert call(base, '/' + name)[1]['data'] == changed
    routing.switch('train', 'module')
    assert call(base, '/' + name)[1]['data'] == changed
    assert call(base, '/' + name, 'DELETE')[1]['status'] == 1
    print('Train rollback passed: module create, legacy read/update, module write gate, return and cleanup')
finally:
    try:
        if call(base, '/' + name)[1].get('status') == 1:
            call(base, '/' + name, 'DELETE')
    finally:
        if routing.DEFS['train']['file'].exists() and __import__('json').loads(
                routing.DEFS['train']['file'].read_text())['mode'] == 'legacy':
            routing.switch('train', 'module')
