import argparse

from utils.constants import SERVER_DEFAULT_TARGET_IP, SERVER_DEFAULT_TARGET_PORT
from utils.validations import validate_ipv4, validate_port


class ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Server application for Reliable UDP project. Receives a udp message from a client under custom reliable protocol."
        )

        parser.add_argument(
            "--listen-ip",
            "-i",
            type=validate_ipv4,
            default=SERVER_DEFAULT_TARGET_IP,
            help="IPv4 address to bind the server.",
        )
        parser.add_argument(
            "--listen-port",
            "-p",
            type=validate_port,
            default=SERVER_DEFAULT_TARGET_PORT,
            help="Port number to listen on.",
        )

        args = parser.parse_args()

        self.listen_ip: str = args.listen_ip
        self.listen_port: int = args.listen_port

    def __str__(self):
        return f"Listen IP: {self.listen_ip}, Listen Port: {self.listen_port}"

    def __repr__(self):
        return self.__str__()
