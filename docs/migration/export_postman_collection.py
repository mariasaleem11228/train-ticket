"""Export every host HTTP mapping as a Postman v2.1 collection.

Run from anywhere: python docs/migration/export_postman_collection.py
The controller source is authoritative; this exporter deliberately does not
invent URLs for the two modules with no HTTP controller.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'ts-modulith/src/main/java/trainticket'
OUTPUT = ROOT / 'docs/migration/postman/TrainTicket-Modulith.postman_collection.json'
MAPPING = re.compile(r'@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\b')
METHODS = {'GetMapping': 'GET', 'PostMapping': 'POST', 'PutMapping': 'PUT',
           'DeleteMapping': 'DELETE', 'PatchMapping': 'PATCH'}
MODULES = ('station orders orderother config seat security train route price basic '
           'travel travel2 routeplan travelplan contacts preserve preserveother '
           'execute payment insidepayment cancel rebook assurance consignprice '
           'consign foodmap food notification verifycode auth user adminbasic '
           'adminroute admintravel adminorder adminuser voucher news ticketoffice '
           'avatar delivery fooddelivery ticketinfo waitorder tripcatalog').split()
READ_ONLY_POST = ('/trips/left', '/trips/routes', '/trip_detail', '/routePlan/',
                  '/travelPlan/', '/order/query', '/orderOther/query',
                  '/order/refresh', '/orderOther/refresh', '/tickets',
                  '/stations/idlist', '/stations/namelist', '/getSpecificOffices',
                  '/users/login', '/seats/left_tickets', '/basic/travel',
                  '/ticketinfo')
SIDE_EFFECT_GET = ('/cancel/{orderId}/{loginId}', '/execute/collected/',
                   '/execute/execute/', '/assurances/{type}/{orderId}',
                   '/order/status/', '/orderOther/status/',
                   '/inside_payment/drawback/', '/inside_payment/{userId}/{money}',
                   '/test_send_delivery', '/test_send_mail', '/test_send_mq')
VARIABLE_DEFAULTS = {
    'baseUrl': 'http://localhost:18080', 'token': '', 'adminToken': '', 'username': '',
    'password': '', 'verificationCode': '', 'accountId': '', 'contactId': '',
    'orderId': '', 'tripId': 'D1345', 'trainNumber': 'D1345',
    'date': '', 'travelDate': '', 'price': '50.0', 'routeId': '',
    'trainTypeId': 'DongCheOne', 'stationId': 'shanghai',
    'newUserId': '', 'newOrderId': '', 'newUsername': 'migration_postman_user',
    'newPassword': '', 'avatarImageBase64': '',
    'from': 'Shang Hai', 'to': 'Su Zhou',
    'stationName': 'Shang Hai', 'startStation': 'Shang Hai',
    'endStation': 'Su Zhou', 'start': 'shanghai', 'end': 'nanjing',
    'trainType': 'DongCheOne', 'weight': '1', 'isWithinRegion': 'true',
    'type': '1', 'status': '0', 'money': '50.0',
    'routeStartId': 'shanghai', 'routeEndId': 'nanjing',
    'allowMutations': 'false',
}
# Values visible directly in Postman's Body tab. IDs owned by a user's test run
# remain variables and are filled by login, catalogue reads, or the tester.
BODY_SAMPLE_VALUES = {
    'from': 'Shang Hai', 'to': 'Su Zhou', 'date': '2026-10-05',
    'travelDate': '2026-10-05', 'tripId': 'D1345',
    'trainNumber': 'D1345', 'trainTypeId': 'DongCheOne',
    'routeStartId': 'shanghai', 'routeEndId': 'nanjing', 'price': '50.0',
}
EXAMPLES = {
    'Station': {'id': '{{stationId}}', 'name': '{{from}}', 'stayTime': 5},
    'Config': {'name': 'migration.test.setting', 'value': 'sample',
               'description': 'Postman migration test'},
    'SecurityConfig': {'id': 'migration-test', 'name': 'migration.test.setting',
                       'value': 'sample', 'description': 'Postman migration test'},
    'TrainType': {'id': '{{trainTypeId}}', 'economyClass': 100,
                  'confortClass': 50, 'averageSpeed': 200},
    'PriceConfig': {'id': '', 'trainType': '{{trainTypeId}}',
                    'routeId': '{{routeId}}', 'basicPriceRate': 0.1,
                    'firstClassPriceRate': 0.2},
    'RouteInfo': {'id': '', 'startStation': '{{routeStartId}}',
                  'endStation': '{{routeEndId}}',
                  'stationList': '{{routeStartId}},{{routeEndId}}',
                  'distanceList': '0,100'},
    'TravelInfo': {'tripId': '{{tripId}}', 'trainTypeId': '{{trainTypeId}}',
                   'routeId': '{{routeId}}', 'startingStationId': '{{routeStartId}}',
                   'stationsId': '{{routeStartId}},{{routeEndId}}',
                   'terminalStationId': '{{routeEndId}}',
                   'startingTime': '10:00', 'endTime': '11:00'},
    'RoutePlanInfo': {'formStationName': '{{from}}', 'toStationName': '{{to}}',
                      'travelDate': '{{date}}', 'num': 3},
    'TransferQuery': {'fromStationName': '{{from}}', 'viaStationName': 'Nan Jing',
                      'toStationName': '{{to}}', 'travelDate': '{{date}}',
                      'trainType': '{{trainTypeId}}'},
    'TripQuery': {'startingPlace': '{{from}}', 'endPlace': '{{to}}',
                  'departureTime': '{{date}}'},
    'SeatRequest': {'travelDate': '{{date}}', 'trainNumber': '{{trainNumber}}',
                    'startStation': '{{from}}', 'destStation': '{{to}}', 'seatType': 2},
    'TravelPlanQuery': {'startingPlace': '{{from}}', 'endPlace': '{{to}}',
                        'departureTime': '{{date}}'},
    'OrderInfo': {'loginId': '{{accountId}}', 'enableStateQuery': False,
                  'enableTravelDateQuery': False, 'enableBoughtDateQuery': False},
    'QueryInfo': {'loginId': '{{accountId}}', 'travelDateStart': '{{date}}',
                  'travelDateEnd': '{{date}}', 'boughtDateStart': '{{date}}',
                  'boughtDateEnd': '{{date}}', 'state': 0,
                  'enableTravelDateQuery': False, 'enableBoughtDateQuery': False,
                  'enableStateQuery': False},
    'Order': {'id': '{{newOrderId}}', 'boughtDate': '{{date}}',
              'travelDate': '{{date}}', 'travelTime': '10:00',
              'accountId': '{{accountId}}', 'contactsName': 'Migration Test Passenger',
              'documentType': 1, 'contactsDocumentNumber': 'MIGRATION-TEST-001',
              'trainNumber': '{{trainNumber}}', 'coachNumber': 1,
              'seatClass': 2, 'seatNumber': '3A', 'from': '{{from}}',
              'to': '{{to}}', 'status': 0, 'price': '{{price}}'},
    'Contact': {'id': '{{contactId}}', 'accountId': '{{accountId}}',
                'name': 'Migration Test Passenger', 'documentType': 1,
                'documentNumber': 'MIGRATION-TEST-001', 'phoneNumber': '15500000000'},
    'PaymentRequest': {'id': '', 'orderId': '{{orderId}}',
                       'userId': '{{accountId}}', 'price': '{{price}}'},
    'AccountRequest': {'userId': '{{accountId}}', 'money': '100.0'},
    'RebookInfo': {'loginId': '{{accountId}}', 'orderId': '{{orderId}}',
                   'oldTripId': '{{tripId}}', 'tripId': '{{tripId}}',
                   'seatType': 2, 'date': '{{date}}'},
    'ConsignPrice': {'id': '', 'index': 1, 'initialWeight': 1,
                     'initialPrice': 10, 'withinPrice': 2, 'beyondPrice': 3},
    'ConsignRequest': {'id': '', 'orderId': '{{orderId}}',
                       'accountId': '{{accountId}}', 'handleDate': '{{date}}',
                       'targetDate': '{{date}}', 'from': '{{from}}', 'to': '{{to}}',
                       'consignee': 'Migration Test Passenger', 'phone': '15500000000',
                       'weight': 1, 'isWithin': True},
    'NotifyInfo': {'id': '', 'sendStatus': False, 'email': 'migration-test@example.test',
                   'orderNumber': '{{orderId}}', 'username': 'Migration Test Passenger',
                   'startingPlace': '{{from}}', 'endPlace': '{{to}}',
                   'startingTime': '10:00', 'date': '{{date}}', 'seatClass': '1',
                   'seatNumber': '3A', 'price': '{{price}}'},
    'FoodDeliveryOrder': {'id': '', 'stationFoodStoreId': '',
                          'foodList': 'Spicy hot noodles', 'tripId': '{{tripId}}',
                          'seatNo': 3, 'createdTime': '{{date}}',
                          'deliveryTime': '{{date}}', 'deliveryFee': 2.5},
    'WaitOrderRequest': {'accountId': '{{accountId}}', 'contactsId': '{{contactId}}',
                         'tripId': '{{tripId}}', 'seatType': 2, 'date': '{{date}}',
                         'from': '{{from}}', 'to': '{{to}}', 'price': '{{price}}'},
    'Seat': {'travelDate': '{{date}}', 'trainNumber': '{{trainNumber}}'},
    'BookingRequest': {'accountId': '{{accountId}}', 'contactsId': '{{contactId}}',
                       'tripId': '{{tripId}}', 'seatType': 2, 'date': '{{date}}',
                       'from': '{{from}}', 'to': '{{to}}', 'assurance': 0,
                       'foodType': 0, 'stationName': '', 'storeName': '',
                       'foodName': '', 'foodPrice': 0, 'handleDate': '',
                       'consigneeName': '', 'consigneePhone': '',
                       'consigneeWeight': 0, 'isWithin': False},
    'InsidePaymentRequest': {'userId': '{{accountId}}', 'orderId': '{{orderId}}',
                             'tripId': '{{tripId}}', 'price': '{{price}}'},
    'FoodOrder': {'orderId': '{{orderId}}', 'foodType': 1,
                  'stationName': '', 'storeName': '', 'foodName': 'Spicy hot noodles',
                  'price': 5},
}

USER_EXAMPLE = {'userId': '{{newUserId}}', 'userName': '{{newUsername}}',
                'password': '{{newPassword}}', 'gender': 1, 'documentType': 1,
                'documentNum': 'MIGRATION-TEST-001',
                'email': 'migration-test@example.test'}
OFFICE_LOCATION = {'province': 'Shanghai', 'city': 'Shanghai',
                   'region': 'Pudong New Area'}
PATH_EXAMPLES = {
    ('POST', '/api/v1/stationservice/stations/idlist'): ['{{from}}', '{{to}}'],
    ('POST', '/api/v1/stationservice/stations/namelist'): ['{{routeStartId}}', '{{routeEndId}}'],
    ('POST', '/api/v1/basicservice/basic/travel'):
        {'startingPlace': '{{from}}', 'endPlace': '{{to}}',
         'trip': {'trainTypeId': '{{trainTypeId}}', 'routeId': '{{routeId}}'}},
    ('POST', '/api/v1/ticketinfoservice/ticketinfo'):
        {'startingPlace': '{{from}}', 'endPlace': '{{to}}',
         'trip': {'trainTypeId': '{{trainTypeId}}', 'routeId': '{{routeId}}'}},
    ('POST', '/api/v1/travelservice/trips/routes'): ['{{routeId}}'],
    ('POST', '/api/v1/travel2service/trips/routes'): ['{{routeId}}'],
    ('POST', '/api/v1/foodmapservice/foodstores'): ['{{routeStartId}}', '{{routeEndId}}'],
    ('POST', '/api/v1/auth'): {'userId': '{{newUserId}}',
                              'userName': '{{newUsername}}', 'password': '{{newPassword}}'},
    ('POST', '/api/v1/users/login'):
        {'username': '{{username}}', 'password': '{{password}}',
         'verificationCode': '{{verificationCode}}'},
    ('POST', '/api/v1/userservice/users/register'): USER_EXAMPLE,
    ('PUT', '/api/v1/userservice/users'): USER_EXAMPLE,
    ('POST', '/api/v1/adminuserservice/users'): USER_EXAMPLE,
    ('PUT', '/api/v1/adminuserservice/users'): USER_EXAMPLE,
    ('POST', '/getVoucher'): {'orderId': '{{orderId}}', 'type': 1},
    ('POST', '/office/getSpecificOffices'): OFFICE_LOCATION,
    ('POST', '/office/addOffice'):
        {**OFFICE_LOCATION, 'office': {'officeName': 'Migration Test Office',
                                      'address': '1 Test Street', 'workTime': '09:00-17:00',
                                      'windowNum': 1}},
    ('POST', '/office/deleteOffice'):
        {**OFFICE_LOCATION, 'officeName': 'Migration Test Office'},
    ('POST', '/office/updateOffice'):
        {**OFFICE_LOCATION, 'oldOfficeName': 'Migration Test Office',
         'newOffice': {'officeName': 'Migration Test Office Updated',
                       'address': '2 Test Street', 'workTime': '09:00-17:00',
                       'windowNum': 1}},
    ('POST', '/api/v1/avatar'): {'img': '{{avatarImageBase64}}'},
    ('POST', '/api/v1/avatar/'): {'img': '{{avatarImageBase64}}'},
    ('PUT', '/api/v1/fooddeliveryservice/orders/dtime'):
        {'orderId': '{{orderId}}', 'deliveryTime': '{{date}}'},
    ('PUT', '/api/v1/fooddeliveryservice/orders/seatno'):
        {'orderId': '{{orderId}}', 'seatNo': 3},
    ('PUT', '/api/v1/fooddeliveryservice/orders/tripid'):
        {'orderId': '{{orderId}}', 'tripId': '{{tripId}}'},
}


def annotation(text, match):
    """Return annotation arguments and source position after its closing paren."""
    pos = match.end()
    if pos >= len(text) or text[pos] != '(':
        return '', pos
    start, depth, quoted, escaped = pos + 1, 1, False, False
    pos += 1
    while pos < len(text):
        char = text[pos]
        if escaped:
            escaped = False
        elif char == '\\' and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    return text[start:pos], pos + 1
        pos += 1
    raise ValueError('Unclosed mapping annotation')


def paths(args):
    if not args.strip():
        return ['']
    named = re.search(r'\b(?:path|value)\s*=\s*', args)
    expression = args[named.end():] if named else args
    # A path itself may contain braces, while an annotation may supply an
    # array of paths. Stop only at a comma outside strings and path arrays.
    depth, quoted, escaped = 0, False, False
    for offset, char in enumerate(expression):
        if escaped:
            escaped = False
        elif char == '\\' and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            elif char == ',' and depth == 0:
                expression = expression[:offset]
                break
    result = re.findall(r'"((?:\\.|[^"\\])*)"', expression)
    return result or ['']


def join(base, path):
    value = '/' + '/'.join(part.strip('/') for part in (base, path) if part.strip('/'))
    if path.endswith('/') and value != '/':
        value += '/'
    return value if value != '/' else '/'


def body_type(signature):
    match = re.search(r'@RequestBody(?:\([^)]*\))?\s+(?:final\s+)?([\w<>?, ]+?)\s+\w+\s*[,)]', signature)
    return match.group(1).strip() if match else None


def dto_file(route, name):
    local = SOURCE / route['module'] / (name + '.java')
    if local.exists():
        return local
    controller = ROOT / route['source']
    imported = re.search(r'import\s+(trainticket(?:\.\w+)+\.' + re.escape(name) + r');',
                         controller.read_text(encoding='utf-8'))
    if imported:
        candidate = ROOT / 'ts-modulith/src/main/java' / Path(
            imported.group(1).replace('.', '/') + '.java')
        if candidate.exists():
            return candidate
    candidates = list(SOURCE.rglob(name + '.java'))
    return candidates[0] if len(candidates) == 1 else None


def field_value(name, java_type):
    alias = {'accountId': 'accountId', 'userId': 'accountId',
             'contactsId': 'contactId', 'contactId': 'contactId',
             'tripId': 'tripId', 'trainNumber': 'trainNumber',
             'orderId': 'orderId', 'startingPlace': 'from',
             'endPlace': 'to', 'from': 'from', 'to': 'to',
             'startStation': 'from', 'destStation': 'to',
             'travelDate': 'date', 'departureTime': 'date', 'date': 'date',
             'price': 'price'}
    if name in alias:
        return '{{' + alias[name] + '}}'
    if java_type in ('boolean', 'Boolean'):
        return False
    if java_type in ('int', 'Integer', 'long', 'Long', 'double', 'Double',
                     'float', 'Float', 'short', 'Short'):
        return 0
    if java_type.startswith(('List<', 'Set<')):
        return []
    if java_type.startswith('Map<'):
        return {}
    return ''


def dto_example(route, java_type):
    if java_type in EXAMPLES:
        return EXAMPLES[java_type]
    if java_type.startswith(('List<', 'Set<')):
        return []
    simple = java_type.split('<', 1)[0]
    file = dto_file(route, simple)
    if not file:
        return {}
    text = file.read_text(encoding='utf-8')
    record = re.search(r'\brecord\s+' + re.escape(simple) + r'\s*\(', text)
    if record:
        start = record.end()
        depth = 1
        pos = start
        while depth and pos < len(text):
            if text[pos] == '(':
                depth += 1
            elif text[pos] == ')':
                depth -= 1
            pos += 1
        components = text[start:pos - 1]
        components = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', components)
        fields = re.findall(r'([\w<>?]+)\s+(\w+)\s*(?:,|$)', components)
    else:
        fields = re.findall(r'(?m)^\s*private\s+(?!static\b)(?:final\s+)?'
                            r'([\w<>?]+)\s+(\w+)\s*(?:=[^;]*)?;', text)
    return {name: field_value(name, kind) for kind, name in fields}


def inline_sample_data(value):
    if isinstance(value, dict):
        return {key: inline_sample_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [inline_sample_data(item) for item in value]
    if isinstance(value, str):
        for key, sample in BODY_SAMPLE_VALUES.items():
            value = value.replace('{{' + key + '}}', sample)
    return value


def mappings():
    found = []
    for file in SOURCE.rglob('*.java'):
        text = file.read_text(encoding='utf-8')
        if '@RestController' not in text:
            continue
        class_match = re.search(r'\bclass\s+\w+', text[text.index('@RestController'):])
        if not class_match:
            raise ValueError('Missing controller class: ' + str(file))
        class_pos = text.index('@RestController') + class_match.start()
        annotations = [(match, *annotation(text, match)) for match in MAPPING.finditer(text)]
        class_paths = ['']
        for match, args, end in annotations:
            if match.start() < class_pos and match.group(1) == 'RequestMapping':
                class_paths = paths(args)
        module = file.relative_to(SOURCE).parts[0]
        for match, args, end in annotations:
            if match.start() < class_pos:
                continue
            kind = match.group(1)
            if kind == 'RequestMapping':
                raise ValueError('Unhandled method-level @RequestMapping: ' + str(file))
            method = METHODS[kind]
            next_body = text.find('{', end)
            signature = text[end:next_body] if next_body >= 0 else ''
            request_body = body_type(signature)
            line = text.count('\n', 0, match.start()) + 1
            for base in class_paths:
                for path in paths(args):
                    found.append({'module': module, 'method': method,
                                  'path': join(base, path), 'body_type': request_body,
                                  'source': str(file.relative_to(ROOT)).replace('\\', '/'),
                                  'line': line})
    return sorted(found, key=lambda x: (MODULES.index(x['module']), x['path'], x['method']))


def variable_path(path):
    return re.sub(r'\{([^{}]+)\}', r'{{\1}}', path).replace('/**', '/{{wildcardPath}}')


def is_mutation(route):
    path, method = route['path'], route['method']
    if method in ('PUT', 'PATCH', 'DELETE'):
        return True
    if method == 'GET':
        return any(marker in path for marker in SIDE_EFFECT_GET)
    if method == 'POST':
        return not any(marker in path for marker in READ_ONLY_POST)
    return False


def needs_admin(route):
    path, method, module = route['path'], route['method'], route['module']
    if module in ('adminroute', 'admintravel', 'adminorder', 'adminuser'):
        return True
    if module == 'adminbasic':
        return not (method == 'GET' and path.rsplit('/', 1)[-1] in
                    ('contacts', 'stations', 'trains', 'configs', 'prices'))
    if module == 'station' and path == '/api/v1/stationservice/stations':
        return method in ('POST', 'PUT', 'DELETE')
    if module in ('orders', 'orderother') and path.endswith('/admin'):
        return method in ('POST', 'PUT')
    if module == 'travel' and method in ('PUT', 'DELETE'):
        return True
    if module == 'auth' and path == '/api/v1/users':
        return method == 'GET'
    if module == 'auth' and path.startswith('/api/v1/users/'):
        return method == 'DELETE'
    return False


def request_item(route):
    path, method = route['path'], route['method']
    vars = re.findall(r'\{([^{}]+)\}', path)
    body = route['body_type']
    destructive = is_mutation(route)
    notes = [f"Source: `{route['source']}:{route['line']}`."]
    if vars:
        notes.append('Set path variables: ' + ', '.join('`' + var + '`' for var in vars) + '.')
    if body:
        notes.append(f'Java request body type: `{body}`. Sample data is illustrative; use IDs and dates from your deployment for dependent requests.')
    if destructive:
        notes.append('May change data. Set `allowMutations=true` only in a disposable test environment.')
    else:
        notes.append('Inspect both HTTP status and response body; 200 alone may contain a business error.')
    path_url = variable_path(path)
    request = {
        'method': method,
        'header': [],
        'url': {'raw': '{{baseUrl}}' + path_url,
                'host': ['{{baseUrl}}'],
                'path': [part for part in path_url.strip('/').split('/') if part]},
        'description': '\n\n'.join(notes),
    }
    if path in ('/api/v1/users/login', '/api/v1/verifycode/generate'):
        request['auth'] = {'type': 'noauth'}
    elif needs_admin(route):
        notes.append('Requires an admin JWT in collection variable `adminToken`.')
        request['auth'] = {'type': 'bearer', 'bearer': [
            {'key': 'token', 'value': '{{adminToken}}', 'type': 'string'}]}
        request['description'] = '\n\n'.join(notes)
    if body:
        example = PATH_EXAMPLES.get((method, path), dto_example(route, body))
        if path == '/api/v1/routeservice/routes' and method == 'POST':
            example = EXAMPLES['RouteInfo']
            notes.append('Route fields use station IDs, such as `shanghai`; distances are comma-separated integers with one value per station.')
            request['description'] = '\n\n'.join(notes)
        request['header'].append({'key': 'Content-Type', 'value': 'application/json'})
        request['body'] = {'mode': 'raw', 'raw': json.dumps(inline_sample_data(example), indent=2),
                           'options': {'raw': {'language': 'json'}}}
    item = {'name': method + ' ' + path, 'request': request,
            'event': [{'listen': 'test', 'script': {'type': 'text/javascript',
                       'exec': ["pm.test('HTTP success', () => pm.expect(pm.response.code).to.be.within(200, 299));"]}}]}
    if destructive:
        item['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript',
            'exec': ["if (pm.collectionVariables.get('allowMutations') !== 'true') pm.execution.skipRequest();"]}})
    if path == '/api/v1/routeservice/routes' and method == 'POST':
        item['event'][1]['script']['exec'].extend([
            "if (!pm.collectionVariables.get('routeStartId') || !pm.collectionVariables.get('routeEndId')) pm.execution.skipRequest();",
        ])
        item['event'][0]['script']['exec'].append(
            "pm.test('Route saved', () => pm.expect(pm.response.json().status).to.eql(1));")
    if path in ('/api/v1/avatar', '/api/v1/avatar/'):
        item['event'][1]['script']['exec'].append(
            "if (!pm.collectionVariables.get('avatarImageBase64')) pm.execution.skipRequest();")
    if path == '/api/v1/users/login':
        item['event'][0]['script']['exec'].extend([
            "const result = pm.response.json();",
            "if (result.status === 1 && result.data?.token) {",
            "  pm.collectionVariables.set('token', result.data.token);",
            "  pm.collectionVariables.set('accountId', result.data.userId);",
            "}",
        ])
    if path == '/api/v1/routeservice/routes' and method == 'GET':
        item['event'][0]['script']['exec'].extend([
            "const rows = pm.response.json().data;",
            "if (!pm.collectionVariables.get('routeId') && Array.isArray(rows) && rows[0]?.id)",
            "  pm.collectionVariables.set('routeId', rows[0].id);",
        ])
    if path == '/api/v1/contactservice/contacts/account/{accountId}':
        item['event'][0]['script']['exec'].extend([
            "const rows = pm.response.json().data;",
            "if (!pm.collectionVariables.get('contactId') && Array.isArray(rows) && rows[0]?.id)",
            "  pm.collectionVariables.set('contactId', rows[0].id);",
        ])
    return item


def collection(routes):
    grouped = defaultdict(list)
    for route in routes:
        grouped[route['module']].append(route)
    if set(grouped) != set(MODULES) - {'delivery', 'tripcatalog'}:
        raise ValueError('Controller modules differ from 45-module manifest: ' +
                         str(set(grouped) ^ (set(MODULES) - {'delivery', 'tripcatalog'})))
    variables = dict(VARIABLE_DEFAULTS)
    for route in routes:
        for key in re.findall(r'\{([^{}]+)\}', route['path']):
            variables.setdefault(key, '')
    variables.setdefault('wildcardPath', 'news')
    folders = []
    for module in MODULES:
        entries = grouped[module]
        if not entries:
            folders.append({'name': module, 'description': 'Internal module; no HTTP controller.',
                            'item': []})
            continue
        folders.append({'name': module,
                        'description': f'{len(entries)} HTTP mappings from the `{module}` module.',
                        'item': [request_item(route) for route in entries]})
    return {
        'info': {'name': 'TrainTicket Spring Modulith — complete module API inventory',
                 '_postman_id': '436bcc11-91b5-4c88-9d05-434e9f235e91',
                 'description': ('Generated from the 45-module host controllers. '
                                 '43 modules expose HTTP endpoints; Delivery and Trip Catalog are internal. '
                                 'Default base URL is the host on port 18080. See POSTMAN.md before running.'),
                 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
        'auth': {'type': 'bearer', 'bearer': [{'key': 'token', 'value': '{{token}}', 'type': 'string'}]},
        'variable': [{'key': key, 'value': value, 'type': 'string'}
                     for key, value in sorted(variables.items())],
        'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': [
            "if (!pm.collectionVariables.get('date')) {",
            "  const day = new Date(); day.setUTCDate(day.getUTCDate() + 7);",
            "  pm.collectionVariables.set('date', day.toISOString().slice(0, 10));",
            "}",
            "if (!pm.collectionVariables.get('travelDate'))",
            "  pm.collectionVariables.set('travelDate', pm.collectionVariables.get('date'));",
            "if (!pm.collectionVariables.get('checkDate'))",
            "  pm.collectionVariables.set('checkDate', pm.collectionVariables.get('date'));",
            "if (!pm.collectionVariables.get('newUserId'))",
            "  pm.collectionVariables.set('newUserId', pm.variables.replaceIn('{{$guid}}'));",
            "if (!pm.collectionVariables.get('newOrderId'))",
            "  pm.collectionVariables.set('newOrderId', pm.variables.replaceIn('{{$guid}}'));",
        ]}}],
        'item': folders,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Fail if the committed collection differs from controller mappings')
    args = parser.parse_args()
    routes = mappings()
    keys = [(route['module'], route['method'], route['path']) for route in routes]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate module/method/path mapping')
    result = json.dumps(collection(routes), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != result:
            raise SystemExit('Postman collection is stale; rerun export_postman_collection.py')
        print(f'PASS Postman collection covers {len(routes)} HTTP mappings across 43 modules')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(result, encoding='utf-8')
        print(f'Exported {len(routes)} HTTP mappings across 43 controller modules to {OUTPUT}')


if __name__ == '__main__':
    main()
