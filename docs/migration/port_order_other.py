"""Port deployed 0.2.0 OrderOther classes recovered with CFR into the host.

Input is the local legacy JAR under target/legacy-order-other. The generated
source is checked into the migration workspace and can be reviewed normally.
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / 'ts-modulith/target/legacy-order-other/src/other'
dest = root / 'ts-modulith/src/main/java/trainticket/orderother'
assert source.is_dir(), 'First decompile the deployed OrderOther JAR with CFR'
dest.mkdir(parents=True, exist_ok=True)
(dest / 'internal').mkdir(exist_ok=True)

for file in (source / 'entity').glob('*.java'):
    data = file.read_text()
    data = data[data.index('package other.entity;'):]
    data = data.replace('package other.entity;', 'package trainticket.orderother;')
    data = data.replace('import other.entity.', 'import trainticket.orderother.')
    data = data.replace('import javax.validation.', 'import jakarta.validation.')
    data = re.sub(r'import org.springframework.data[^;]+;\n', '', data)
    data = re.sub(r'@Document\([^\n]+\)\n|@Id\s*\n', '', data)
    (dest / file.name).write_text('/* Deployed codewisdom OrderOther 0.2.0 DTO. */\n' + data)

interface = (source / 'service/OrderOtherService.java').read_text()
interface = interface[interface.index('package other.service;'):]
interface = interface.replace('package other.service;', 'package trainticket.orderother;')
interface = interface.replace('import edu.fudan.common.util.Response;\n', '')
interface = interface.replace('import org.springframework.http.HttpHeaders;\n', '')
interface = interface.replace('import other.entity.', 'import trainticket.orderother.')
interface = interface.replace('import other.service.OrderOtherService;\n', '')
interface = interface.replace('OrderOtherService', 'OrderOtherOperations').replace('Response', 'OrderOtherResult')
interface = re.sub(r', HttpHeaders var\d+', '', interface)
interface = re.sub(r'HttpHeaders var\d+, ', '', interface)
interface = re.sub(r'\(HttpHeaders var\d+\)', '()', interface)
(dest / 'OrderOtherOperations.java').write_text(interface)
(dest / 'OrderOtherResult.java').write_text('''package trainticket.orderother;
public class OrderOtherResult<T> {
    private final Integer status;
    private final String msg;
    private final T data;
    public OrderOtherResult(Integer status, String msg, T data) { this.status=status; this.msg=msg; this.data=data; }
    public Integer getStatus() { return status; }
    public String getMsg() { return msg; }
    public T getData() { return data; }
}
''')

service = (source / 'service/OrderOtherServiceImpl.java').read_text()
service = service[service.index('package other.service;'):]
service = service.replace('package other.service;', 'package trainticket.orderother.internal;')
service = service.replace('import edu.fudan.common.util.Response;\n', '')
service = service.replace('import other.entity.', 'import trainticket.orderother.')
service = service.replace('import other.repository.OrderOtherRepository;\n', '')
service = service.replace('import other.service.OrderOtherService;\n', '')
service = service.replace('import edu.fudan.common.util.Response;\n', 'import trainticket.orderother.OrderOtherResult;\n') if 'import edu.fudan.common.util.Response;\n' in service else service.replace('import java.util.ArrayList;', 'import trainticket.orderother.OrderOtherResult;\nimport java.util.ArrayList;')
service = re.sub(r'import org.springframework.(core.ParameterizedTypeReference|http.HttpEntity|http.HttpHeaders|http.HttpMethod|http.ResponseEntity|web.client.RestTemplate);\n', '', service)
service = service.replace('OrderOtherServiceImpl', 'OrderOtherApplicationService')
service = service.replace('implements OrderOtherService', 'implements trainticket.orderother.OrderOtherOperations')
service = service.replace('Response', 'OrderOtherResult')
service = re.sub(r'\s*@Autowired\s*private RestTemplate restTemplate;', '', service)
service = re.sub(r', HttpHeaders headers', '', service)
service = service.replace('(HttpHeaders headers)', '()')
service = service.replace(', headers)', ')').replace('(headers)', '()')
service = service.replace('this.orderOtherRepository.save((Object)', 'this.orderOtherRepository.save(')
service = service.replace('ArrayList list =', 'ArrayList<Order> list =')
service = service.replace('ArrayList orders =', 'ArrayList<Order> orders =')
service = service.replace('ArrayList<Order> orders = (ArrayList)', 'ArrayList<Order> orders = (ArrayList<Order>)')
start = service.index('    public List<String> queryForStationId(')
end = service.index('    public OrderOtherResult saveChanges', start)
service = service[:start] + '''    public List<String> queryForStationId(List<String> ids) {
        return (List<String>) stations.namesForIds(ids).getData();
    }

''' + service[end:]
service = service.replace('    private static final Logger LOGGER', '    @Autowired private trainticket.station.StationOperations stations;\n    private static final Logger LOGGER')
service = service.replace('    @Autowired\n    private OrderOtherRepository orderOtherRepository;\n    @Autowired private trainticket.station.StationOperations stations;',
'''    private final OrderOtherRepository orderOtherRepository;
    private final trainticket.station.StationOperations stations;
    public OrderOtherApplicationService(OrderOtherRepository orderOtherRepository,
                                        trainticket.station.StationOperations stations) {
        this.orderOtherRepository=orderOtherRepository;
        this.stations=stations;
    }''')
service = service.replace('@Service\n', '@Service\n@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")\n')
assert 'HttpHeaders' not in service and 'RestTemplate' not in service and 'import other.entity' not in service, [term for term in ('HttpHeaders','RestTemplate','import other.entity') if term in service]
(dest / 'internal/OrderOtherApplicationService.java').write_text('/* Ported from deployed codewisdom/ts-order-other-service:0.2.0. */\n' + service)

controller = (source / 'controller/OrderOtherController.java').read_text()
controller = controller[controller.index('package other.controller;'):]
controller = controller.replace('package other.controller;', 'package trainticket.orderother.internal;')
controller = controller.replace('import other.entity.', 'import trainticket.orderother.')
controller = controller.replace('import other.service.OrderOtherService;', 'import trainticket.orderother.OrderOtherOperations;')
controller = controller.replace('OrderOtherService orderService', 'OrderOtherOperations orderService')
controller = controller.replace('import org.springframework.http.HttpHeaders;\n', '').replace('import org.springframework.web.bind.annotation.RequestHeader;\n', '')
controller = re.sub(r', @RequestHeader HttpHeaders headers', '', controller)
controller = controller.replace('(@RequestHeader HttpHeaders headers)', '()')
controller = controller.replace(', headers)', ')').replace('(headers)', '()')
controller = controller.replace('@RestController\n', '@RestController\n@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")\n')
assert 'HttpHeaders' not in controller
(dest / 'internal/OrderOtherController.java').write_text('/* Deployed 0.2.0 OrderOther HTTP contract. */\n' + controller)

repository = (root / 'ts-modulith/src/main/java/trainticket/orders/internal/OrderRepository.java').read_text()
repository = repository.replace('package trainticket.orders.internal;', 'package trainticket.orderother.internal;')
repository = repository.replace('import trainticket.orders.Order;', 'import trainticket.orderother.Order;')
repository = repository.replace('class OrderRepository', 'class OrderOtherRepository')
repository = repository.replace('OrderRepository(', 'OrderOtherRepository(')
repository = repository.replace('modulith.orders.enabled', 'modulith.order-other.enabled')
repository = repository.replace('modulith.orders.mongo-uri', 'modulith.order-other.mongo-uri')
repository = repository.replace('modulith.orders.writes-enabled', 'modulith.order-other.writes-enabled')
repository = repository.replace('ownership.permits("orders")', 'ownership.permits("orderother")')
repository = repository.replace('Orders writes disabled', 'OrderOther writes disabled')
repository = repository.replace('Orders database required', 'OrderOther database required')
repository = repository.replace('order.entity.Order', 'other.entity.Order')
repository = repository.replace('    @PreDestroy void close()', '    @PreDestroy void close()')
(dest / 'internal/OrderOtherRepository.java').write_text(repository)
print('Generated OrderOther DTO, operations, service and controller from deployed release')
