import argparse

from utils.constants import (
    CLIENT_DEFAULT_TARGET_IP,
    CLIENT_DEFAULT_TARGET_PORT,
    CLIENT_DEFAULT_TIMEOUT,
)
from utils.validations import validate_ipv4, validate_port, validate_range


class ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Client application of the Reliable UDP project. Sends messages to a server under custom reliable protocol."
        )

        parser.add_argument(
            "input",
            type=str,
            nargs="?",
            help="STD input msg or input buffer to send to server",
        )

        parser.add_argument(
            "--target",
            "--target-ip",
            "-i",
            type=validate_ipv4,
            default=CLIENT_DEFAULT_TARGET_IP,
            help="IPv4 address of the server.",
        )

        parser.add_argument(
            "--port",
            "--target-port",
            "-p",
            type=validate_port,
            default=CLIENT_DEFAULT_TARGET_PORT,
            help="Port number of the server.",
        )

        parser.add_argument(
            "--timeout",
            "-t",
            type=validate_range(min=0),
            default=CLIENT_DEFAULT_TIMEOUT,
            help="Timeout for client",
        )

        args = parser.parse_args()

        self.input = args.input
        self.target: str = args.target
        self.target_port: int = args.port
        self.timeout: int = args.timeout

    def __str__(self):
        return f"Input: {self.input}, Target: {self.target}, Port: {self.target_port}, Timeout: {self.timeout}"

    def __repr__(self):
        return self.__str__()
