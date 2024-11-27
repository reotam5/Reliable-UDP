from utils.reliableUDP import ReliableUDP
import argparse

from utils.validations import validate_ipv4, validate_port

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Server application for Reliable UDP project. Receives a udp message from a client under custom reliable protocol."
    )
    parser.add_argument(
        "--listen-ip",
        required=True,
        type=validate_ipv4,
        help="IPv4 address to bind the server.",
    )
    parser.add_argument(
        "--listen-port",
        required=True,
        type=validate_port,
        help="Port number to listen on.",
    )
    args = parser.parse_args()


    reliableUDP = ReliableUDP().create()
    reliableUDP.bind(args.listen_ip, args.listen_port)
    while True:
        message = reliableUDP.recv()
        if message:
            print(message)

