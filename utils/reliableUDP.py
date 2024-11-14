import ipaddress
from socket import AF_INET, SOCK_DGRAM, socket 
from typing import Any 
from utils.packet import Packet 
from utils.fsm import FSM


class ReliableUDP():
    BUFFER_SIZE = 1024

    def __init__(self):
        self.socket: socket
        self.seq_num = 0
        self.ack_num = 0
        self.target_addr: Any
        self.timeout = 0.1 


    def create(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        return self


    def bind(self, host, port: int):
        self.socket.bind((
            str(ipaddress.ip_address(host)),
            port
        ))


    def connect(self, server_ip: str, server_port: int):
        print('CONNECT')
        def send_syn():
            self.target_addr = (str(ipaddress.ip_address(server_ip)), server_port)
            self.seq_num = 1
            syn_packet = Packet()
            syn_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            syn_packet.set_header_field("syn", "1", base=2)
            self.socket.sendto(syn_packet.to_byte(), self.target_addr)
            self.seq_num += 1
            return "WAIT_SYN_ACK"

        def wait_syn_ack():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "SEND_SYN"
                packet = Packet(data)
                is_syn = packet.get_header_field("syn", base=2) == "1"
                is_ack = packet.get_header_field("ack", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                if is_syn and is_ack and ack_num >= self.seq_num:
                    self.ack_num = seq_num + 1
                    return "SEND_ACK"
                else:
                    return "SEND_SYN"
            except TimeoutError:
                return "SEND_SYN"

        def send_ack():
            ack_packet = Packet()
            ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(ack_packet.to_byte(), self.target_addr)
            return FSM.STATE.EXIT


        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_SYN", "action": send_syn },
                { "source": "SEND_SYN", "dest": "WAIT_SYN_ACK", "action": wait_syn_ack },
                { "source": "WAIT_SYN_ACK", "dest": "SEND_ACK", "action": send_ack },
                { "source": "WAIT_SYN_ACK", "dest": "SEND_SYN", "action": send_syn },
                { "source": "SEND_ACK", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="SEND_SYN",
        )
        fsm.run()


    def accept(self):
        print('ACCEPT')
        def wait_syn():
            self.socket.settimeout(None)
            data, addr = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
            packet = Packet(data)
            is_syn = packet.get_header_field("syn", base=2) == "1"
            seq_num = int(packet.get_header_field("seq_num", base=10))
            if is_syn:
                self.target_addr = addr
                self.ack_num = seq_num + 1 
                return "SEND_SYN_ACK"
            else:
                return "WAIT_SYN"

        def send_syn_ack():
            self.seq_num = 1
            syn_ack_packet = Packet()
            syn_ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            syn_ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            syn_ack_packet.set_header_field("syn", "1", base=2)
            syn_ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(syn_ack_packet.to_byte(), self.target_addr)
            self.seq_num += 1
            return "WAIT_ACK"

        def wait_ack():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "SEND_SYN_ACK"
                packet = Packet(data)
                is_ack = packet.get_header_field("ack", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                if is_ack and ack_num == self.seq_num:
                    return FSM.STATE.EXIT
                else:
                    return "SEND_SYN_ACK"
            except TimeoutError:
                return "SEND_SYN_ACK"

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "WAIT_SYN", "action": wait_syn },
                { "source": "WAIT_SYN", "dest": "WAIT_SYN", "action": wait_syn },
                { "source": "WAIT_SYN", "dest": "SEND_SYN_ACK", "action": send_syn_ack },
                { "source": "SEND_SYN_ACK", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "SEND_SYN_ACK", "action": send_syn_ack },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="WAIT_SYN",
        )
        fsm.run()


    def send(self, message: str):
        print('SEND', message)
        tmp_seq_num = self.seq_num
        tmp_ack_num = self.ack_num
        message_packet = Packet()
        message_packet.set_header_field("seq_num", str(tmp_seq_num), base=10)
        message_packet.set_header_field("ack_num", str(tmp_ack_num), base=10)
        message_packet.set_payload(message)
        self.seq_num += len(message)

        def send_data():
            self.socket.sendto(message_packet.to_byte(), self.target_addr)
            return "WAIT_ACK"

        def wait_ack():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "SEND_DATA"
                packet = Packet(data)
                is_ack = packet.get_header_field("ack", base=2) == "1"
                is_syn = packet.get_header_field("syn", base=2) == "1"
                ack_num = int(packet.get_header_field("ack_num", base=10))
                if is_syn:
                    self.connect(self.target_addr[0], self.target_addr[1])
                    return "SEND_DATA"
                if is_ack and ack_num == self.seq_num:
                    print("SENT", message)
                    return FSM.STATE.EXIT
                else:
                    return "SEND_DATA"
            except TimeoutError:
                return "SEND_DATA"

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_DATA", "action": send_data },
                { "source": "SEND_DATA", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "SEND_DATA", "action": send_data },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="SEND_DATA",
        )
        fsm.run()


    def send_all(self, message: str):
        size = 1
        chunks = [message[i:i+size] for i in range(0, len(message), size)]
        for chunk in chunks:
            self.send(chunk)

    def close_server(self, message):
        print("CLOSE")
        fin_packet = Packet()
        fin_packet.set_header_field("seq_num", str(self.seq_num), base=10)
        fin_packet.set_header_field("ack_num", str(self.ack_num), base=10)
        fin_packet.set_header_field("fin", "1", base=2)
        self.seq_num += 1

        def send_fin():
            self.socket.sendto(fin_packet.to_byte(), self.target_addr)
            return "WAIT_ACK"

        def wait_ack():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "SEND_FIN"
                packet = Packet(data)
                is_ack = int(packet.get_header_field("ack", base=2))
                is_fin = int(packet.get_header_field("fin", base=2))
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                if ack_num >= self.seq_num:
                    if is_fin:
                        self.ack_num = seq_num + 1
                        return "SEND_ACK"
                    if is_ack:
                        return FSM.STATE.EXIT
                else:
                    return "SEND_FIN"
            except TimeoutError:
                return FSM.STATE.EXIT

        def send_ack():
            ack_packet = Packet()
            ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(ack_packet.to_byte(), self.target_addr)
            return "SEND_FIN"

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_FIN", "action": send_fin },
                { "source": "SEND_FIN", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "WAIT_ACK", "dest": "SEND_ACK", "action": send_ack },
                { "source": "SEND_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "WAIT_ACK", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="SEND_FIN",
            verbose=True
        )
        fsm.run()
        return message

    def receive(self):
        print("RECEIVE")
        def wait_data(previous_message = ""):
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                packet = Packet(data)
                seq_num = int(packet.get_header_field("seq_num", base=10))
                is_fin = packet.get_header_field("fin", base=2) == "1"
                payload = packet.get_payload() or ""
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "WAIT_DATA"
                if is_fin:
                    self.ack_num = seq_num + 1
                if seq_num == self.ack_num:
                    if not is_fin:
                        print("RECEIVED: ", payload)
                    self.ack_num = seq_num + len(payload)
                    return ("SEND_ACK", previous_message + payload, is_fin)
                return ("SEND_ACK", previous_message, is_fin)
            except TimeoutError:
                return "WAIT_DATA"

        def send_ack(message, is_fin):
            ack_packet = Packet()
            ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(ack_packet.to_byte(), self.target_addr)
            if is_fin:
                return (FSM.STATE.EXIT, message)
            else:
                return ("WAIT_DATA", message)


        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "WAIT_DATA", "action": wait_data },
                { "source": "WAIT_DATA", "dest": "SEND_ACK", "action": send_ack },
                { "source": "WAIT_DATA", "dest": "WAIT_DATA", "action": wait_data },
                { "source": "SEND_ACK", "dest": "WAIT_DATA", "action": wait_data },
                { "source": "SEND_ACK", "dest": FSM.STATE.EXIT, "action": lambda message: self.close_server(message) },
            ],
            initial_state="WAIT_DATA",
        )
        return fsm.run()


    def close(self):
        print("CLOSE")
        fin_packet = Packet()
        fin_packet.set_header_field("seq_num", str(self.seq_num), base=10)
        fin_packet.set_header_field("ack_num", str(self.ack_num), base=10)
        fin_packet.set_header_field("fin", "1", base=2)
        self.seq_num += 1

        def send_fin():
            self.socket.sendto(fin_packet.to_byte(), self.target_addr)
            return "WAIT_ACK"

        def wait_ack():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "SEND_FIN"
                packet = Packet(data)
                ack_num = int(packet.get_header_field("ack_num", base=10))
                if ack_num >= self.seq_num:
                    return "WAIT_FIN"
                else:
                    return "SEND_FIN"
            except TimeoutError:
                return "SEND_FIN"

        def wait_fin():
            try:
                self.socket.settimeout(self.timeout)
                data, (ip, port) = self.socket.recvfrom(ReliableUDP.BUFFER_SIZE)
                if ip != self.target_addr[0] or port != self.target_addr[1]:
                    return "WAIT_FIN"
                packet = Packet(data)
                is_fin = int(packet.get_header_field("fin", base=2))
                ack_num = int(packet.get_header_field("ack_num", base=10))
                seq_num = int(packet.get_header_field("seq_num", base=10))
                if is_fin and ack_num >= self.seq_num:
                    self.ack_num = seq_num + 1
                    return "SEND_ACK"
                else:
                    return "WAIT_FIN"
            except TimeoutError:
                return "CLEAN_UP"

        def send_ack():
            ack_packet = Packet()
            ack_packet.set_header_field("seq_num", str(self.seq_num), base=10)
            ack_packet.set_header_field("ack_num", str(self.ack_num), base=10)
            ack_packet.set_header_field("ack", "1", base=2)
            self.socket.sendto(ack_packet.to_byte(), self.target_addr)
            return "CLEAN_UP"

        def clean_up():
            self.socket.close()
            return FSM.STATE.EXIT

        fsm = FSM(
            [
                { "source": FSM.STATE.START, "dest": "SEND_FIN", "action": send_fin },
                { "source": "SEND_FIN", "dest": "WAIT_ACK", "action": wait_ack },
                { "source": "WAIT_ACK", "dest": "WAIT_FIN", "action": wait_fin },
                { "source": "WAIT_ACK", "dest": "SEND_FIN", "action": send_fin },
                { "source": "WAIT_FIN", "dest": "WAIT_FIN", "action": wait_fin },
                { "source": "WAIT_FIN", "dest": "CLEAN_UP", "action": clean_up },
                { "source": "WAIT_FIN", "dest": "SEND_ACK", "action": send_ack },
                { "source": "SEND_ACK", "dest": "CLEAN_UP", "action": clean_up },
                { "source": "CLEAN_UP", "dest": FSM.STATE.EXIT, "action": None },
            ],
            initial_state="SEND_FIN",
            verbose=True
        )
        fsm.run()


