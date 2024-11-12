import ipaddress
import sys
from socket import AF_INET, socket, SOCK_DGRAM
import random
import time
from typing import Any 


class Proxy():
    def __init__(self, listen_ip, listen_port: int, target_ip: str, target_port: int, client_drop: int, client_delay: int, client_delay_time: float, server_drop: float, server_delay: float, server_delay_time: float):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.client_drop = client_drop
        self.client_delay = client_delay
        self.client_delay_time = client_delay_time
        self.server_drop = server_drop
        self.server_delay = server_delay
        self.server_delay_time = server_delay_time
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.client_addr: Any


    def run(self):
        self.socket.bind((str(ipaddress.ip_address(self.listen_ip)), self.listen_port))
        while True:
            data, (ip, port) = self.socket.recvfrom(65535)
            is_server = ip == self.target_ip and port == self.target_port
            if not is_server:
                self.client_addr = (ip, port)
            forward_to = (str(ipaddress.ip_address(self.client_addr[0] if is_server else self.target_ip)), self.client_addr[1] if is_server else self.target_port)
            print('==============')
            print('received from ', (ip, port))
            print('forwarding to ', forward_to)
            print('==============')
            drop_prob = self.server_drop if is_server else self.client_drop
            delay_prob = self.server_delay if is_server else self.client_delay
            delay_time = self.server_delay_time if is_server else self.client_delay_time
            
            shouldDrop = random.random() <= (drop_prob / 100)
            shouldDelay = random.random() <= (delay_prob / 100)
            if shouldDrop:
                continue
            if shouldDelay:
                time.sleep(delay_time / 1000)
            self.socket.sendto(data, forward_to)
        


if __name__ == "__main__":
    proxy = Proxy(
        listen_ip="0.0.0.0",
        listen_port=4000,
        target_ip="127.0.0.1",
        target_port=5000,
        client_drop=80,
        client_delay=80,
        client_delay_time=1000,
        server_drop=80,
        server_delay=80,
        server_delay_time=1000,
    )
    proxy.run()



