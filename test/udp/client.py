import socket
import time

from argparser import Parser


def main():
    args = Parser()
    print(args)
    for pings in range(50):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(1.0)
        message = b"test"
        addr = (args.target, args.port)

        start = time.time()
        client_socket.sendto(message, addr)
        try:
            data, server = client_socket.recvfrom(1024)
            end = time.time()
            elapsed = end - start
            print(f"{data} {pings} {elapsed}")
        except socket.timeout:
            print("REQUEST TIMED OUT")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
