# consul_client.py
import consul
import socket

class ConsulClient:
    def __init__(self, host='localhost', port=8500):
        self.consul = consul.Consul(host=host, port=port)

    def register_service(self, service_name, service_port, service_tags=None):
        """
        注册服务到Consul
        """
        service_id = f'{service_name}-{socket.gethostname()}'
        service_address = socket.gethostbyname(socket.gethostname())
        service_check = consul.Check.http(url=f'http://{service_address}:{service_port}/health', interval='10s')
        self.consul.agent.service.register(name=service_name, service_id=service_id, address=service_address, port=service_port, tags=service_tags, check=service_check)
        return service_id

    def update_key_value(self, dict_to_upload: dict):
        """
        将字典上传Consul
        """
        for key, value in dict_to_upload.items():
            self.consul.kv.put(key, str(value))

    def download_key_value(self, key: str):
        """
        从Consul下载指定的Key Value
        """
        index, data = self.consul.kv.get(key)
        if data:
            return data['Value'].decode()
        else:
            return None

    def deregister_service(self, service_id):
        """
        从Consul中注销服务
        """
        self.consul.agent.service.deregister(service_id)

    def discover_services(self, service_name):
        """
        发现服务
        """
        services = self.consul.catalog.service(service_name)[1]
        return [(service['ServiceAddress'], service['ServicePort']) for service in services]

    def check_port_available(self, sname: str, sip: str, sport: int):
        if sip == '0.0.0.0' or sip == '127.0.0.1':
            sip = socket.gethostbyname(socket.gethostname())
        # 获取所有已注册的服务
        services = self.consul.agent.services()

        # 遍历所有已注册的服务，获取它们的 IP 和端口号
        service_instances = {}
        for service_id in services:
            service_name = services[service_id]['Service']
            _, instances = self.consul.health.service(service_name, passing=True)
            for instance in instances:
                ip = instance['Service']['Address']
                port = instance['Service']['Port']
                if service_name not in service_instances:
                    service_instances[service_name] = []
                service_instances[service_name].append((ip, port))
        
        # 逐个检查服务列表和对应的实例 IP 和端口号
        for name, instances in service_instances.items():
            for ip, port in instances:
                if sip == ip and sport == port and sname != name:
                    print(f'{ip}:{port}已被{name}占用')
                    return False
        return True

consul_client = ConsulClient()
