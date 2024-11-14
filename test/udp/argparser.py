import argparse
import ipaddress
import sys

DEFAULT_PORT = 12000


class Parser:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Port Scanner")
        parser.add_argument(
            "target", type=validate_ipv4, help="Target IP address to scan."
        )

        parser.add_argument(
            "--port",
            "-p",
            type=validate_port,
            default=DEFAULT_PORT,
            help=f"Port (default: {DEFAULT_PORT})",
        )

        args = parser.parse_args()

        self.port: int = args.port
        self.target: str = args.target

    def __str__(self):
        return f"Target: {self.target}\n" f"Port: {self.port}\n"

    def __repr__(self):
        return self.__str__()


def validate_port(value):
    try:
        port = int(value)
        if not 0 < port < 65535:
            raise ValueError
        return port
    except:
        sys.exit(
            f"Invalid port number: {value}. Port needs to be an integer between 1 and 65535"
        )


def validate_ipv4(value):
    try:
        ip = ipaddress.ip_address(str(value))
        if not ip.version == 4:
            raise ValueError
        return str(value)
    except:
        sys.exit(f"Invalid IPv4 address format: {value}.")


def validate_greater_than(value, min: int):
    try:
        num = int(value)
        if num < min:
            raise ValueError
        return num
    except:
        sys.exit(
            f"Invalid number {value}. Value needs to be an integer greater than or equal to {min}."
        )
