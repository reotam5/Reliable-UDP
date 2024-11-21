import ipaddress
from socket import AF_INET, SOCK_DGRAM, socket 
from typing import Any 
from utils.packet import Packet 
from utils.fsm import FSM
import random


class ReliableUDP():
    BUFFER_SIZE = 1024

    def __init__(self):
        self.socket: socket
        self.timeout = 1
        self.timeout_disconnect = 10
        self.random_int = 0
        self.random_int_peer = 0
        self.message_pointer = 0
        self.payload_size = 1
        self.target_addr: Any = None

    def create(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        return self

    def bind(self, ip, port):
        self.socket.bind((str(ipaddress.ip_address(ip)), port))

    def send(self, message, ip, port):
        self.message_pointer = 0
        self.random_int_peer = 0
        self.random_int = random.randint(1, 1000)

        def send_data(retry = self.timeout_disconnect // self.timeout):
            if self.message_pointer == len(message):
                return "WAIT_FIN"
            packet = Packet()
            packet.set_header_field("seq_num", str(self.random_int + self.message_pointer), base=10)
            packet.set_header_field("ack_num", str(self.random_int_peer), base=10)
            message_end_pointer = min(self.message_pointer + self.payload_size, len(message))
            if self.message_pointer == 0:
                packet.set_header_field("syn", "1", base=2)
            if message_end_pointer == len(message):
                packet.set_header_field("fin", "1", base=2)
            packet.set_payload(message[self.message_pointer:message_end_pointer])
            self.socket.sendto(packet.to_byte(), (str(ip), port))
            return ("WAIT_ACK", retry)

        def wait_ack(retry):
            if retry < 0:
                print('timeout')
                return FSM.STATE.EXIT
            try:
                self.socket.settimeout(self.timeout)
                data, _ = self.socket.recvfrom(1024)
                packet = Packet(data)
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                is_valid = ack_num - self.random_int == self.message_pointer + 1
                is_ack = is_valid and packet.get_header_field("ack", base=2) == "1"
                is_fin = is_valid and packet.get_header_field("fin", base=2) == "1"
                is_rst = packet.get_header_field("rst", base=2) == "1"
                if is_rst:
                    return FSM.STATE.EXIT
                if is_ack:
                    if self.message_pointer == 0:
                        self.random_int_peer = seq_num
                    self.message_pointer = ack_num - self.random_int
                if is_fin:
                    return "SEND_ACK"
                return ("SEND_DATA")
            except TimeoutError:
                return ("SEND_DATA", retry - 1)

        def wait_fin():
            try:
                self.socket.settimeout(self.timeout)
                data, _ = self.socket.recvfrom(1024)
                packet = Packet(data)
                is_fin = packet.get_header_field("fin", base=2) == "1"
                if is_fin:
                    return "SEND_ACK"
                return "WAIT_FIN"
            except TimeoutError:
                return FSM.STATE.EXIT

        def send_ack():
            packet = Packet()
            packet.set_header_field("seq_num", str(self.message_pointer + self.random_int + 1), base=10)
            packet.set_header_field("ack_num", str(self.random_int_peer + 1), base=10)
            packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(packet.to_byte(), (str(ipaddress.ip_address(ip)), port))
            return FSM.STATE.EXIT
            

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_DATA", "action": send_data },
                { "source": "SEND_DATA", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "SEND_DATA", "action": send_data },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": None },
                { "source": "WAIT_ACK", "dest": "SEND_ACK", "action": send_ack },
                { "source": "SEND_DATA", "dest": "WAIT_FIN", "action": wait_fin },
                { "source": "WAIT_FIN", "dest": "SEND_ACK", "action": send_ack },
                { "source": "WAIT_FIN", "dest": "WAIT_FIN", "action": wait_fin },
                { "source": "WAIT_FIN", "dest": FSM.STATE.EXIT, "action": None },
                { "source": "SEND_ACK", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="SEND_DATA",
        )
        fsm.run()


    def recv(self):
        self.message_pointer = 0
        self.random_int_peer = 0
        self.random_int = random.randint(1, 1000)

        def receive_data(prev_message = ""):
            self.socket.settimeout(None)
            data, addr = self.socket.recvfrom(1024)
            packet = Packet(data)
            seq_num = int(packet.get_header_field("seq_num", base=10))
            payload = packet.get_payload() or ""
            is_last_message = packet.get_header_field("fin", base=2) == "1"
            is_first_message = packet.get_header_field("syn", base=2) == "1"

            if is_first_message and len(prev_message) == 0:
                self.message_pointer = 0
                self.target_addr = addr
                self.random_int_peer = seq_num

            if self.random_int_peer == 0:
                return "SEND_RST"

            if seq_num - self.random_int_peer == self.message_pointer:
                self.message_pointer = len(prev_message + payload)
                return ("SEND_ACK", prev_message + payload, is_last_message)
            return ("SEND_ACK", prev_message, False)

        def send_rst():
            if not self.target_addr:
                return "RECEIVE_DATA"
            packet = Packet()
            packet.set_header_field("rst", "1", base=2)
            self.socket.sendto(packet.to_byte(), self.target_addr)
            return "RECEIVE_DATA"

        def send_ack(acknowledged_message, is_last_message):
            if not self.target_addr:
                return ("RECEIVE_DATA", "")
            packet = Packet()
            packet.set_header_field("ack", "1", base=2)
            packet.set_header_field("seq_num", str(self.random_int), base=10)
            packet.set_header_field("ack_num", str(self.random_int_peer + len(acknowledged_message)), base=10)
            self.socket.sendto(packet.to_byte(), self.target_addr)
            
            if is_last_message:
                return ("SEND_FIN", acknowledged_message)
            return ("RECEIVE_DATA", acknowledged_message)

        def send_fin(message):
            packet = Packet()
            packet.set_header_field("fin", "1", base=2)
            packet.set_header_field("seq_num", str(self.random_int), base=10)
            packet.set_header_field("ack_num", str(self.random_int_peer + len(message)), base=10)
            self.socket.sendto(packet.to_byte(), self.target_addr)
            return ("WAIT_ACK", message)

        def wait_ack(message):
            try:
                self.socket.settimeout(self.timeout)
                data, _ = self.socket.recvfrom(1024)
                packet = Packet(data)
                is_ack = packet.get_header_field("ack", base=2) == "1"
                is_syn = packet.get_header_field("syn", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                if is_syn or (is_ack and ack_num == self.random_int + 1):
                    return (FSM.STATE.EXIT, message)
                return ("SEND_FIN", message)
            except:
                return (FSM.STATE.EXIT, message)

        def clean_up(message):
            self.message_pointer = 0 
            self.random_int_peer = 0 
            self.random_int = 0
            return message


        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "RECEIVE_DATA", "dest": "SEND_ACK", "action": send_ack },
                { "source": "RECEIVE_DATA", "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "RECEIVE_DATA", "dest": "SEND_RST", "action": send_rst },
                { "source": "RECEIVE_DATA", "dest": FSM.STATE.EXIT, "action": clean_up },
                { "source": "SEND_RST", "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "SEND_ACK", "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "SEND_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "SEND_FIN", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "WAIT_ACK", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": clean_up },
            ],
            initial_state="RECEIVE_DATA",
        )
        return fsm.run()

    def close(self):
        self.socket.close()

