import sys
import argparse
from utils.reliableUDP import ReliableUDP
from utils.validations import validate_ipv4, validate_port, validate_range


def main():
    parser = argparse.ArgumentParser(
        description="Client application of the Reliable UDP project. Sends messages to a server under custom reliable protocol."
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="std input msg or input buffer to send to server",
    )
    parser.add_argument(
        "--target-ip",
        required=True,
        type=validate_ipv4,
        help="IPv4 address of the server.",
    )
    parser.add_argument(
        "--target-port",
        required=True,
        type=validate_port,
        help="Port number of the server.",
    )
    parser.add_argument(
        "--timeout",
        required=True,
        type=validate_range(min=0),
        help="Port number of the server.",
    )
    args = parser.parse_args()


    reliableUDP = ReliableUDP(timeout=args.timeout).create()
    send = lambda x: reliableUDP.send(x, args.target_ip, args.target_port)

    if args.input:
        # Command-line argument provided
        send(args.input)
    elif not sys.stdin.isatty():
        # Input is being piped or redirected
        std_input = sys.stdin.read()
        send(std_input)
    else:
        # Interactive user input
        print("Enter your input (type 'exit' to finish):")
        while True:
            try:
                line = input()
                if line.lower() == "exit":
                    break
                send(line)
            except (KeyboardInterrupt, EOFError):
                break

    reliableUDP.close()


if __name__ == "__main__":
    main()
    sys.exit(0)
