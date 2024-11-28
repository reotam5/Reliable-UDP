import sys

from utils.client.argparser import ArgParser
from utils.reliableUDP import ReliableUDP


def main():
    parser = ArgParser()
    print("Client arguments:")
    print(parser)
    print("")

    reliableUDP = ReliableUDP(timeout=parser.timeout).create()
    send = lambda x: reliableUDP.send(x, parser.target, parser.target_port)

    if parser.input:
        # Command-line argument provided
        send(parser.input)
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
