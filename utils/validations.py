import ipaddress
import sys


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
