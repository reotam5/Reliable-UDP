import sys

from utils.reliableUDP import ReliableUDP
from utils.server.argparser import ArgParser


def main():
    parser = ArgParser()
    print("Server arguments:")
    print(parser)
    print("")

    reliableUDP = ReliableUDP().create()
    reliableUDP.bind(parser.listen_ip, parser.listen_port)
    while True:
        message = reliableUDP.recv()
        if message:
            print(message)


if __name__ == "__main__":
    main()
    sys.exit(0)
