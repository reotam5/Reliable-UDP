import ipaddress
from socket import AF_INET, SOCK_DGRAM, socket 
from typing import Any, Optional
from utils.packet import Packet 


class ReliableUDP():
    BUFFER_SIZE = 1024

    def __init__(self):
        self.socket: socket
        self.seq_num = 0
        self.ack_num = 0
        self.target_addr: Any
        self.timeout = 1 


    def create(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        return self


    def bind(self, host, port: int):
        self.socket.bind((
            str(ipaddress.ip_address(host)),
            port
        ))


    def connect(self, server_ip: str, server_port: int):
        self.seq_num = 0
        self.ack_num = 0
        self.target_addr = (str(ipaddress.ip_address(server_ip)), server_port)
        syn_packet = Packet()
        syn_packet.set_header_field("seq_num", str(self.seq_num), base=10)
        syn_packet.set_header_field("syn", "1", base=2)
        self.socket.sendto(syn_packet.to_byte(), self.target_addr)

        while True:
            try:
                self.socket.settimeout(self.timeout)
                data, addr = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                packet = Packet(data)
                is_syn = packet.get_header_field("syn", base=2) == "1"
                is_ack = packet.get_header_field("ack", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                if is_syn and is_ack and ack_num == self.seq_num + 1:
                    self.ack_num = seq_num + 1
                    self.seq_num += 1

                    ack_packet = Packet()
                    ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
                    ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
                    ack_packet.set_header_field("ack", "1", base=2)
                    self.socket.sendto(ack_packet.to_byte(), addr)
                    return True

            except TimeoutError:
                self.socket.sendto(syn_packet.to_byte(), self.target_addr)


    def accept(self):
        self.seq_num = 0
        self.ack_num = 0
        while True:
            data, addr = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
            packet = Packet(data)
            is_syn = packet.get_header_field("syn", 2) == "1"
            seq_num = int(packet.get_header_field("seq_num", base=10))
            if is_syn:
                self.target_addr = addr
                self.ack_num = seq_num + 1

                syn_ack_packet = Packet()
                syn_ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
                syn_ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
                syn_ack_packet.set_header_field("syn", "1", base=2)
                syn_ack_packet.set_header_field("ack", "1", base=2)
                self.socket.sendto(syn_ack_packet.to_byte(), self.target_addr)

                try:
                    self.socket.settimeout(self.timeout)
                    data, addr = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                    packet = Packet(data)
                    is_syn = packet.get_header_field("syn", base=2) == "1"
                    is_ack = packet.get_header_field("ack", base=2) == "1"
                    ack_num = int(packet.get_header_field("ack_num", base=10))
                    seq_num = int(packet.get_header_field("seq_num", base=10))
                    if is_ack and ack_num == self.seq_num + 1:
                        self.seq_num += 1
                        return self

                except TimeoutError:
                    continue


    def send(self, message: str):
        message_packet = Packet()
        message_packet.set_header_field("seq_num", str(self.seq_num), base=10)
        message_packet.set_header_field("ack_num", str(self.ack_num), base=10)
        message_packet.set_payload(message)
        print("SENDING", message)

        while True:
            self.socket.sendto(message_packet.to_byte(), self.target_addr)

            try:
                self.socket.settimeout(self.timeout)
                data, _ = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                packet = Packet(data)
                is_ack = packet.get_header_field("ack", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                if is_ack and ack_num == self.seq_num + len(message_packet.get_hex()):
                    self.seq_num += len(message_packet.get_hex())
                    break

            except TimeoutError:
                continue

    def send_all(self, message: str):
        size = 10
        chunks = [message[i:i+size] for i in range(0, len(message), size)]
        for chunk in chunks:
            self.send(chunk)


    def receive(self, timeout: Optional[float] = None):
        while True:
            self.socket.settimeout(timeout)
            data, addr = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
            packet = Packet(data)
            seq_num = int(packet.get_header_field("seq_num", base=10))
            is_fin = packet.get_header_field("fin", base=2) == "1"
            payload = packet.get_payload() or ""

            is_valid_data = seq_num == self.ack_num
            if is_valid_data:
                self.ack_num += len(packet.get_hex())
            ack_packet = Packet()
            ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(ack_packet.to_byte(), addr)


            if is_fin:
                fin_seq_num = self.seq_num + 1
                fin_packet = Packet()
                fin_packet.set_header_field("seq_num", str(fin_seq_num), base=10)
                fin_packet.set_header_field("ack_num", str(self.ack_num), base=10)
                fin_packet.set_header_field("fin", "1", base=2)
                self.socket.sendto(fin_packet.to_byte(), self.target_addr)
                return None

            if is_valid_data:
                return payload


    def close(self):
        fin_packet = Packet()
        fin_packet.set_header_field("seq_num", str(self.seq_num), base=10)
        fin_packet.set_header_field("ack_num", str(self.ack_num), base=10)
        fin_packet.set_header_field("fin", "1", base=2)
        self.socket.sendto(fin_packet.to_byte(), self.target_addr)

        is_fin_ack_received = False
        
        while True:
            try:
                self.socket.settimeout(self.timeout)
                data, _ = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                packet = Packet(data)
                ack_num = int(packet.get_header_field("ack_num", base=10))
                is_fin = packet.get_header_field("fin", base=2) == "1"
                is_ack = packet.get_header_field("ack", base=2) == "1"

                if ack_num == self.seq_num + len(fin_packet.get_hex()):
                    if is_ack:
                        is_fin_ack_received = True
                    if is_fin:
                        self.socket.close()
                        break
            except TimeoutError:
                if not is_fin_ack_received:
                    self.socket.sendto(fin_packet.to_byte(), self.target_addr)
                    continue
                else:
                    self.socket.close()
                    break


