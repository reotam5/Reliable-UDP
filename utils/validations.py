import ipaddress
import sys
from typing import Optional


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


def validate_range(min: Optional[float] = None, max: Optional[float] = None):
    def validation(value):
        try:
            num = float(value)
            if min != None:
                if num < min:
                    raise ValueError
            if max != None:
                if num > max:
                    raise ValueError
            return num
        except ValueError:
            if min != None and max != None:
                sys.exit(
                    f"Invalid number {value}. Value needs to be between {min} and {max}."
                )
            if min == None and max != None:
                sys.exit(
                    f"Invalid number {value}. Value needs to be smaller than or equal to {max}."
                )
            if min != None and max == None:
                sys.exit(
                    f"Invalid number {value}. Value needs to be greater than or equal to {min}."
                )
        except:
            sys.exit(f"Invalid number {value}")
    return validation 


def validate_range_input(delimiter="-", min: Optional[float] = None):
    def validation(value):
        try:
            parts = value.split(delimiter)
            first = float(parts[0]) if len(parts) > 0 and parts[0] else None
            second = float(parts[1]) if len(parts) > 1 and parts[1] else None
            if min != None:
                if first and first < min:
                    sys.exit(f"Invalid number {first}. Value needs to be greater than or equal to {min}")
            if second != None:
                if first and second and first >= second:
                    sys.exit(f"Invalid range {value}. First number has to be smaller than the second one.")
            return (first, second)
        except Exception as e:
            print(e)
            sys.exit(f"Invalid input {value}")
    return validation
