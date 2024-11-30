import argparse

from utils.constants import PROXY_LISTEN_IP, PROXY_LISTEN_PORT, PROXY_TARGET_IP, PROXY_TARGET_PORT
from utils.validations import validate_ipv4, validate_port, validate_range, validate_range_input

class ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Proxy that simulates unreliable connection."
        )
        parser.add_argument(
            "--listen-ip",
            "--lip",
            type=validate_ipv4,
            default=PROXY_LISTEN_IP,
            help="IPv4 address to bind the proxy server.",
        )
        parser.add_argument(
            "--listen-port",
            "--lp",
            type=validate_port,
            default=PROXY_LISTEN_PORT,
            help="Port number listening for incoming client packets.",
        )
        parser.add_argument(
            "--target-ip",
            "--tip",
            type=validate_ipv4,
            default=PROXY_TARGET_IP,
            help="IPv4 address of the server to forward packets to.",
        )
        parser.add_argument(
            "--target-port",
            "--tp",
            type=validate_port,
            default=PROXY_TARGET_PORT,
            help="Port number of the server.",
        )
        parser.add_argument(
            "--client-drop",
            default=0,
            type=validate_range(min=0, max=100),
            help="Drop chance(0%% -100%%) for packets from the client.",
        )
        parser.add_argument(
            "--server-drop",
            default=0,
            type=validate_range(min=0, max=100),
            help="Drop chance(0%% -100%%) for packets from the server.",
        )
        parser.add_argument(
            "--client-delay",
            default=0,
            type=validate_range(min=0, max=100),
            help="Delay chance(0%% -100%%) for packets from the client.",
        )
        parser.add_argument(
            "--server-delay",
            default=0,
            type=validate_range(min=0, max=100),
            help="Delay chance(0%% -100%%) for packets from the server.",
        )
        parser.add_argument(
            "--client-delay-time",
            default=(0,0),
            type=validate_range_input(min=0),
            help="Delay time in milliseconds(fixed or range. eg) 1000 for 1 second, or 1000-2000 for 1-2 seconds",
        )
        parser.add_argument(
            "--server-delay-time",
            default=(0,0),
            type=validate_range_input(min=0),
            help="Delay time in milliseconds(fixed or range. eg) 1000 for 1 second, or 1000-2000 for 1-2 seconds",
        )
        args = parser.parse_args()

        self.listen_ip = args.listen_ip
        self.listen_port = args.listen_port
        self.target_ip = args.target_ip
        self.target_port = args.target_port
        self.client_drop = args.client_drop
        self.client_delay = args.client_delay
        self.client_delay_time = args.client_delay_time
        self.server_drop = args.server_drop
        self.server_delay = args.server_delay
        self.server_delay_time = args.server_delay_time


    def __str__(self):
        listening = f"Listening={self.listen_ip}:{self.listen_port}"
        forwarding = f"Forwarding={self.target_ip}:{self.target_port}"
        title = f"Proxy Settings:{listening}||{forwarding}\n\n"
        return title

    def __repr__(self):
        return self.__str__()


