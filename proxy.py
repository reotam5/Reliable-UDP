import ipaddress
import random
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from socket import AF_INET, SOCK_DGRAM, socket
from utils.cli import CLI
from utils.proxy.argparser import ArgParser

class Proxy:
    def __init__(
        self,
        listen_ip,
        listen_port: int,
        target_ip: str,
        target_port: int,
        client_drop: int,
        client_delay: int,
        client_delay_time: tuple[float, float],
        server_drop: float,
        server_delay: float,
        server_delay_time: tuple[float, float],
    ):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.client_config = {
            "ip": None,
            "port": None,
            "drop": client_drop,
            "delay": client_delay,
            "delay_time": client_delay_time,
        }
        self.server_config = {
            "ip": target_ip,
            "port": target_port,
            "drop": server_drop,
            "delay": server_delay,
            "delay_time": server_delay_time,
        }

    def set_config(self, target, field, value):
        config = self.client_config if target == "client" else self.server_config
        config[field] = value

    def get_config(self, target, field):
        config = self.client_config if target == "client" else self.server_config
        return config[field]

    @staticmethod
    def forward(socket, data, forawrd_to, delay):
        if delay:
            time.sleep(delay/1000)
        socket.sendto(data, forawrd_to)

    def recv_packet(self):
        with ThreadPoolExecutor() as executor:
            while True:
                data, (ip, port) = self.socket.recvfrom(1024)
                is_server = (
                    ip == self.server_config["ip"] and port == self.server_config["port"]
                )
                if not is_server:
                    self.client_config["ip"] = ip
                    self.client_config["port"] = port
                forward_to = (
                    str(
                        ipaddress.ip_address(
                            self.client_config["ip"]
                            if is_server
                            else self.server_config["ip"]
                        )
                    ),
                    self.client_config["port"] if is_server else self.server_config["port"],
                )
                config = self.server_config if is_server else self.client_config
                drop_prob = config["drop"]
                delay_prob = config["delay"]
                delay_time_min, delay_time_max = config["delay_time"]
                delay_time = random.uniform(delay_time_min, delay_time_max or delay_time_min)

                should_drop = random.random() <= (drop_prob / 100)
                should_delay = random.random() <= (delay_prob / 100)
                if should_drop:
                    continue
                executor.submit(Proxy.forward, self.socket, data, forward_to, delay_time if should_delay else None)

    def run(self):
        self.socket.bind((str(ipaddress.ip_address(self.listen_ip)), self.listen_port))
        self.recv_packet()

    def stop(self):
        self.socket.close()


def signal_handler(_sig, _frame, proxy: Proxy, cli: CLI):
    print("Shutting down gracefully...")
    proxy.stop()  # Stop the proxy loop
    cli.stop()
    sys.exit(0)


if __name__ == "__main__":
    parser = ArgParser()

    proxy = Proxy(
        listen_ip=parser.listen_ip,
        listen_port=parser.listen_port,
        target_ip=parser.target_ip,
        target_port=parser.target_port,
        client_drop=parser.client_drop,
        client_delay=parser.client_delay,
        client_delay_time=parser.client_delay_time,
        server_drop=parser.server_drop,
        server_delay=parser.server_delay,
        server_delay_time=parser.server_delay_time,
    )
    cli = CLI(
        [
            str(parser),
            "Proxy Parameters",
            "UP/DOWN arrows to select value, LEFT/RIGHT to adjust",
        ],
        [
            {
                "name": "Client drop",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("client", "drop"),
                "set_value": lambda x: proxy.set_config("client", "drop", x),
            },
            {
                "name": "Client delay",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("client", "delay"),
                "set_value": lambda x: proxy.set_config("client", "delay", x),
            },
            {
                "name": "Client delay time - min",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("client", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("client", "delay_time", (min(x, proxy.get_config("client", "delay_time")[1]),proxy.get_config("client", "delay_time")[1])),
            },
            {
                "name": "Client delay time - max",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("client", "delay_time")[1],
                "set_value": lambda x: proxy.set_config("client", "delay_time", (proxy.get_config("client", "delay_time")[0], max(x, proxy.get_config("client", "delay_time")[0]))),
            },
            {
                "name": "Server drop",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("server", "drop"),
                "set_value": lambda x: proxy.set_config("server", "drop", x),
            },
            {
                "name": "Server delay",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("server", "delay"),
                "set_value": lambda x: proxy.set_config("server", "delay", x),
            },
            {
                "name": "Server delay time - min",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("server", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("server", "delay_time", (min(x, proxy.get_config("server", "delay_time")[1]),proxy.get_config("server", "delay_time")[1])),
            },
            {
                "name": "Server delay time - max",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("server", "delay_time")[1],
                "set_value": lambda x: proxy.set_config("server", "delay_time", (proxy.get_config("server", "delay_time")[0],max(x, proxy.get_config("server", "delay_time")[0]))),
            },
        ],
        10,
    )

    # Register signal handler
    signal.signal(
        signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, proxy, cli)
    )

    with ThreadPoolExecutor() as executor:
        executor.submit(proxy.run)
        executor.submit(cli.start)

    executor.shutdown(wait=True)

    sys.exit(0)
