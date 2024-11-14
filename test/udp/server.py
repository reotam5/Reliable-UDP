import random
import socket

from argparser import Parser


def main():
    args = Parser()
    print(args)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((args.target, args.port))

    while True:
        rand = random.randint(0, 10)
        message, address = server_socket.recvfrom(1024)
        message = message.upper()
        if rand >= 4:
            server_socket.sendto(message, address)


if __name__ == "__main__":
    main()
