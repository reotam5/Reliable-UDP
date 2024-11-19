import argparse
import ipaddress
import sys

from utils.client.argparser import ArgParser
from utils.reliableUDP import ReliableUDP


def main():
    args = ArgParser()
    print(args)
    print(args.input)

    reliableUDP = ReliableUDP().create()

    if args.input:
        print("String input")
    elif not sys.stdin.isatty():
        print("Standardin input")
    else:
        sys.exit("No input provided")


if __name__ == "__main__":
    main()
