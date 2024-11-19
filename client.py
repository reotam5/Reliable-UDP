import sys

from utils.client.argparser import ArgParser
from utils.reliableUDP import ReliableUDP


def main():
    args = ArgParser()
    print(args)
    print(args.input)

    reliableUDP = ReliableUDP().create()
    send = lambda x: reliableUDP.send(x, args.target, args.target_port)

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

    # Close the connection
    # TODO: Close connection properly maybe send a reset?
    # reliableUDP.close()


if __name__ == "__main__":
    main()
    sys.exit(0)
