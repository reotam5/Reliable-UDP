import ipaddress
from socket import AF_INET, SOCK_DGRAM, socket 
from typing import Any 
from utils.packet import Packet 
from utils.fsm import FSM
from random import randint

class ReliableUDP():
    BUFFER_SIZE = 1024
    RETRIES = 20

    def __init__(self, timeout=1):
        self.socket: socket
        self.message_pointer = 0 
        self.random_number = 0
        self.prev_random_number = None
        self.payload_size = 1
        self.target_addr: Any = None
        self.retransmission_timeout = timeout

    def create(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        return self

    def bind(self, ip, port):
        self.socket.bind((str(ipaddress.ip_address(ip)), port))

    def flush_recv_buffer(self):
        try:
            self.socket.setblocking(False)
            while _ := self.socket.recvfrom(65535):
                continue
        except BlockingIOError:
            pass
        finally:
            self.socket.setblocking(True)

    def send(self, message, ip, port):
        self.flush_recv_buffer()
        self.message_pointer = 0 
        self.random_number = randint(1, 5000)

        def send_data(retries = ReliableUDP.RETRIES):
            message_end_pointer = min(self.message_pointer + self.payload_size, len(message))
            is_first = self.message_pointer == 0
            is_last = message_end_pointer == len(message)

            if retries < 1:
                if not is_last:
                    print(f"\033[91mMax retires reached({ReliableUDP.RETRIES}) {f"'{message[:self.message_pointer]}'" if self.message_pointer > 0 else ""} \033[0m")
                return FSM.STATE.EXIT

            packet = Packet()
            packet.set_header_field("seq_num", str(self.message_pointer + self.random_number), base=10)
            packet.set_header_field("ack_num", "0", base=10)
            if is_first:
                packet.set_header_field("syn", "1", base=2)
            if is_last:
                packet.set_header_field("fin", "1", base=2)
            packet.set_payload(message[self.message_pointer:message_end_pointer])
            self.socket.sendto(packet.to_byte(), (str(ip), port))
            return ("WAIT_ACK", is_last, message_end_pointer - self.message_pointer, retries - 1)

        def wait_ack(is_last, payload_length, retries):
            try:
                self.socket.settimeout(self.retransmission_timeout)
                data, _ = self.socket.recvfrom(1024)
                packet = Packet(data)
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                is_valid = ack_num == self.random_number + self.message_pointer + payload_length
                is_ack = is_valid and packet.get_header_field("ack", base=2) == "1"
                is_fin = is_valid and packet.get_header_field("fin", base=2) == "1"

                if not is_valid:
                    return ("WAIT_ACK", is_last, payload_length, retries)
                if is_ack:
                    self.message_pointer = ack_num - self.random_number
                if is_fin:
                    return ("SEND_ACK", seq_num)
                if is_last:
                    return ("WAIT_ACK", True, 0, retries)
                return ("SEND_DATA", ReliableUDP.RETRIES if is_valid else retries)
            except TimeoutError:
                return ("SEND_DATA", retries)

        def send_ack(last_seq_num):
            packet = Packet()
            packet.set_header_field("seq_num", str(self.random_number + self.message_pointer), base=10)
            packet.set_header_field("ack_num", str(last_seq_num + 1), base=10)
            packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(packet.to_byte(), (str(ipaddress.ip_address(ip)), port))
            return FSM.STATE.EXIT
            

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_DATA", "action": send_data },
                { "source": "SEND_DATA", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "SEND_DATA", "dest": FSM.STATE.EXIT, "action": self.flush_recv_buffer },
                { "source": "WAIT_ACK", "dest": "SEND_DATA", "action": send_data },
                { "source": "WAIT_ACK", "dest": "SEND_ACK", "action": send_ack },
                { "source": "WAIT_ACK", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "SEND_ACK", "dest": FSM.STATE.EXIT, "action": self.flush_recv_buffer },
            ],
            initial_state="SEND_DATA",
        )
        fsm.run()


    def recv(self):
        self.flush_recv_buffer()
        self.message_pointer = 0
        self.random_number = 0

        def receive_data(prev_message = ""):
            self.socket.settimeout(None)
            data, addr = self.socket.recvfrom(1024)
            packet = Packet(data)
            seq_num = int(packet.get_header_field("seq_num", base=10))
            payload = packet.get_payload() or ""
            is_last_message = packet.get_header_field("fin", base=2) == "1"
            is_syn = packet.get_header_field("syn", base=2) == "1"
            is_valid = (self.message_pointer == 0 and is_syn) or seq_num - self.random_number == self.message_pointer
            is_new_connection = is_syn and not is_valid 
            is_duplicate_syn = is_syn and seq_num == self.prev_random_number

            if is_syn and not is_duplicate_syn:
                self.random_number = seq_num
                self.message_pointer = 0
                self.target_addr = addr
                prev_message = ""

            if (is_valid or is_new_connection) and not is_duplicate_syn:
                self.message_pointer = len(prev_message + payload)
                return ("SEND_ACK", prev_message + payload, is_last_message)
            return ("SEND_ACK", prev_message, False)

        def send_ack(acknowledged_message, is_last_message):
            if not self.target_addr:
                return ("RECEIVE_DATA", "")
            packet = Packet()
            packet.set_header_field("ack", "1", base=2)
            packet.set_header_field("seq_num", "0", base=10)
            packet.set_header_field("ack_num", str(self.random_number + len(acknowledged_message)), base=10)
            self.socket.sendto(packet.to_byte(), self.target_addr)
            
            if is_last_message:
                return ("SEND_FIN", acknowledged_message, 20)
            return ("RECEIVE_DATA", acknowledged_message)

        def send_fin(message, retries):
            if retries < 1:
                return (FSM.STATE.EXIT, message)

            packet = Packet()
            packet.set_header_field("fin", "1", base=2)
            packet.set_header_field("ack", "1", base=2)
            packet.set_header_field("seq_num", "0", base=10)
            packet.set_header_field("ack_num", str(self.random_number + len(message)), base=10)
            self.socket.sendto(packet.to_byte(), self.target_addr)
            return ("WAIT_ACK", message, retries - 1)

        def wait_ack(message, retries):
            try:
                self.socket.settimeout(0.5)
                data, _ = self.socket.recvfrom(1024)
                packet = Packet(data)
                is_ack = packet.get_header_field("ack", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                is_valid = ack_num  == 1
                if is_ack and is_valid:
                    return (FSM.STATE.EXIT, message)
                return ("SEND_FIN", message, retries)
            except TimeoutError:
                return ("SEND_FIN", message, retries)

        def clean_up(message):
            self.message_pointer = 0 
            self.prev_random_number = self.random_number
            self.random_number = 0
            self.flush_recv_buffer()
            return message


        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "RECEIVE_DATA", "dest": "SEND_ACK", "action": send_ack },
                { "source": "SEND_ACK", "dest": "RECEIVE_DATA", "action": receive_data },
                { "source": "SEND_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "SEND_FIN", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "SEND_FIN", "dest": FSM.STATE.EXIT, "action": clean_up },
                { "source": "WAIT_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": clean_up },
            ],
            initial_state="RECEIVE_DATA",
        )
        return fsm.run()

    def close(self):
        self.socket.close()

