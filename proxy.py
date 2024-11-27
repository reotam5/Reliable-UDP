import ipaddress
import random
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from socket import AF_INET, SOCK_DGRAM, socket
from utils.cli import CLI
import argparse

from utils.validations import validate_ipv4, validate_port, validate_range, validate_range_input

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
    parser = argparse.ArgumentParser(
        description="Proxy that simulates unreliable connection."
    )
    parser.add_argument(
        "--listen-ip",
        required=True,
        type=validate_ipv4,
        help="IPv4 address to bind the proxy server.",
    )
    parser.add_argument(
        "--listen-port",
        required=True,
        type=validate_port,
        help="Port number to listen for lcient packets.",
    )
    parser.add_argument(
        "--target-ip",
        required=True,
        type=validate_ipv4,
        help="IPv4 address of the server to forward packets to.",
    )
    parser.add_argument(
        "--target-port",
        required=True,
        type=validate_port,
        help="Port number of the server.",
    )
    parser.add_argument(
        "--client-drop",
        default=0,
        type=validate_range(min=0, max=100),
        help="Drop chance(0% -100%) for packets from the client.",
    )
    parser.add_argument(
        "--server-drop",
        default=0,
        type=validate_range(min=0, max=100),
        help="Drop chance(0% -100%) for packets from the server.",
    )
    parser.add_argument(
        "--client-delay",
        default=0,
        type=validate_range(min=0, max=100),
        help="Delay chance(0% -100%) for packets from the client.",
    )
    parser.add_argument(
        "--server-delay",
        default=0,
        type=validate_range(min=0, max=100),
        help="Delay chance(0% -100%) for packets from the server.",
    )
    parser.add_argument(
        "--client-delay-time",
        default=(0,None),
        type=validate_range_input(min=0),
        help="Delay time in milliseconds(fixed or range. eg) 1000 for 1 second, or 1000-2000 for 1-2 seconds",
    )
    parser.add_argument(
        "--server-delay-time",
        default=(0,None),
        type=validate_range_input(min=0),
        help="Delay time in milliseconds(fixed or range. eg) 1000 for 1 second, or 1000-2000 for 1-2 seconds",
    )
    args = parser.parse_args()


    proxy = Proxy(
        listen_ip=args.listen_ip,
        listen_port=args.listen_port,
        target_ip=args.target_ip,
        target_port=args.target_port,
        client_drop=args.client_drop,
        client_delay=args.client_delay,
        client_delay_time=args.client_delay_time,
        server_drop=args.server_drop,
        server_delay=args.server_delay,
        server_delay_time=args.server_delay_time,
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
                "get_value": lambda: proxy.get_config("client", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("client", "delay_time", (x,None)),
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
                "get_value": lambda: proxy.get_config("server", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("server", "delay_time", (x,None)),
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
