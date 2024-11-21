import ipaddress
import random
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from socket import AF_INET, SOCK_DGRAM, socket
from utils.cli import CLI

class Proxy:
    def __init__(
        self,
        listen_ip,
        listen_port: int,
        target_ip: str,
        target_port: int,
        client_drop: int,
        client_delay: int,
        client_delay_time: float,
        server_drop: float,
        server_delay: float,
        server_delay_time: float,
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
                delay_time = config["delay_time"]

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


def main():
    proxy = Proxy(
        listen_ip="0.0.0.0",
        listen_port=4000,
        target_ip="127.0.0.1",
        target_port=5000,
        client_drop=0,
        client_delay=50,
        client_delay_time=500,
        server_drop=0,
        server_delay=50,
        server_delay_time=500,
    )
    cli = CLI(
        [
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
                "name": "Client delay time",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("client", "delay_time"),
                "set_value": lambda x: proxy.set_config("client", "delay_time", x),
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
                "name": "Server delay time",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("server", "delay_time"),
                "set_value": lambda x: proxy.set_config("server", "delay_time", x),
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


if __name__ == "__main__":
    main()
    sys.exit(0)
