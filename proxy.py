import ipaddress
from socket import AF_INET, socket, SOCK_DGRAM
import random
import time
from concurrent.futures import ThreadPoolExecutor
from utils.cli import CLI


class Proxy():
    def __init__(self, listen_ip, listen_port: int, target_ip: str, target_port: int, client_drop: int, client_delay: int, client_delay_time: float, server_drop: float, server_delay: float, server_delay_time: float):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.client_config = {
            "ip": None,
            "port": None,
            "drop": client_drop,
            "delay": client_delay,
            "delay_time": client_delay_time
        }
        self.server_config = {
            "ip": target_ip,
            "port": target_port,
            "drop": server_drop,
            "delay": server_delay,
            "delay_time": server_delay_time
        }


    def set_config(self, target, field, value):
        config = self.client_config if target == 'client' else self.server_config
        config[field] = value


    def get_config(self, target, field):
        config = self.client_config if target == 'client' else self.server_config
        return config[field]


    def run(self):
        self.socket.bind((str(ipaddress.ip_address(self.listen_ip)), self.listen_port))
        while True:
            data, (ip, port) = self.socket.recvfrom(65535)
            is_server = ip == self.server_config["ip"] and port == self.server_config["port"]
            if not is_server:
                self.client_config["ip"] = ip 
                self.client_config["port"] = port
            forward_to = (str(ipaddress.ip_address(self.client_config["ip"] if is_server else self.server_config["ip"])), self.client_config["port"] if is_server else self.server_config["port"])
            config = self.server_config if is_server else self.client_config
            drop_prob = config["drop"]
            delay_prob = config["delay"]
            delay_time = config["delay_time"]

            shouldDrop = random.random() <= (drop_prob / 100)
            shouldDelay = random.random() <= (delay_prob / 100)
            if shouldDrop:
                continue
            if shouldDelay:
                time.sleep(delay_time / 1000)
            self.socket.sendto(data, forward_to)


if __name__ == "__main__":
    proxy = Proxy(
        listen_ip="0.0.0.0",
        listen_port=4000,
        target_ip="127.0.0.1",
        target_port=5000,
        client_drop=80,
        client_delay=80,
        client_delay_time=1000,
        server_drop=80,
        server_delay=80,
        server_delay_time=1000,
    )
    cli = CLI(
        [
            "Proxy Parameters",
            "UP/DOWN arrows to select value, LEFT/RIGHT to adjust",
        ], 
        [
            {"name": "Client drop", "min": 0, "max": 100, "step": 10, "suffix": "%","get_value": lambda: proxy.get_config("client","drop"), "set_value": lambda x: proxy.set_config("client", "drop", x)},
            {"name": "Client delay", "min": 0, "max": 100, "step": 10, "suffix": "%","get_value": lambda: proxy.get_config("client","delay"), "set_value": lambda x: proxy.set_config("client", "delay", x)},
            {"name": "Client delay time", "min": 0,"step": 100, "suffix": "ms","get_value": lambda: proxy.get_config("client","delay_time"), "set_value": lambda x: proxy.set_config("client", "delay_time", x)},
            {"name": "Server drop", "min": 0, "max": 100, "step": 10, "suffix": "%","get_value": lambda: proxy.get_config("server","drop"), "set_value": lambda x: proxy.set_config("server", "drop", x)},
            {"name": "Server delay", "min": 0, "max": 100, "step": 10, "suffix": "%","get_value": lambda: proxy.get_config("server","delay"), "set_value": lambda x: proxy.set_config("server", "delay", x)},
            {"name": "Server delay time", "min": 0,"step": 100, "suffix": "ms","get_value": lambda: proxy.get_config("server","delay_time"), "set_value": lambda x: proxy.set_config("server", "delay_time", x)},
        ], 
        10
    )

    with ThreadPoolExecutor() as executor:
        executor.submit(proxy.run)
        executor.submit(cli.start)

    executor.shutdown(wait=True)



