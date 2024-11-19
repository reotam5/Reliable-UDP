import argparse

from utils.constants import CLIENT_DEFAULT_TARGET_IP, CLIENT_DEFAULT_TARGET_PORT
from utils.validations import validate_ipv4, validate_port


class ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(description="ReliableUDP client")

        parser.add_argument(
            "input",
            type=str,
            nargs="?",
            help="STD input msg or input buffer to send to server",
        )

        parser.add_argument(
            "-t",
            "--target",
            type=validate_ipv4,
            default=CLIENT_DEFAULT_TARGET_IP,
            help="Target IP address",
        )

        parser.add_argument(
            "-p",
            "--port",
            type=validate_port,
            default=CLIENT_DEFAULT_TARGET_PORT,
            help="Target port",
        )

        args = parser.parse_args()

        self.input = args.input
        self.target: str = args.target
        self.target_port: int = args.port

    def __str__(self):
        return f"Target: {self.target}:{self.target_port}"

    def __repr__(self):
        return self.__str__()
