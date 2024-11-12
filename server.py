from enum import Enum
from typing import Any
from utils.reliableUDP import ReliableUDP
from utils.fsm import FSM
from socket import AF_INET, SO_REUSEADDR, SOCK_DGRAM, SOL_SOCKET, socket, INADDR_ANY 
import ipaddress

from utils.packet import Packet

class Server():
    class STATE(Enum):
        CREATE_SOCKET = "CREATE_SOCKET"
        BIND_SOCKET = "BIND_SOCKET"
        ACCEPT = "ACCEPT"
        ACKNOWLEDGE = "ACKNOWLEDGE"
        RECEIVE = "RECEIVE"
        PROCESS_DATA = "PROCESS_DATA"
        ERROR = "ERROR"
        CLEAN_UP = "CLEAN_UP"

    def __init__(self, port):
        self.port = port
        self.socket: socket
        self.data = b""
        self.ack_num = 0
        self.seq_num = 0
        self.client_addr: Any 

    def create_socket(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        if socket:
            return Server.STATE.BIND_SOCKET
        else:
            return Server.STATE.ERROR

    def bind_socket(self):
        try:
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((
                str(ipaddress.ip_address(INADDR_ANY)),
                self.port,
            ))
            return Server.STATE.RECEIVE
        except:
            return Server.STATE.ERROR
    
    def accept_connection(self):
        try:
            raw, addr = self.socket.recvfrom(65535)
            packet = Packet(raw)
            seq = packet.get_header_field("seq_num", 10)
            syn = packet.get_header_field("syn", 2)
            self.client_addr = addr
            self.ack_num = int(seq) + 1
            if syn == "1":
                return Server.STATE.ACKNOWLEDGE
            else:
                return Server.STATE.ACCEPT

        except:
            return Server.STATE.ERROR 

    def acknowledge(self):
        try:
            acknowledgement = Packet()
            acknowledgement.set_header_field("seq_num", str(self.seq_num), 10)
            acknowledgement.set_header_field("ack_num", str(self.ack_num), 10)
            acknowledgement.set_header_field("syn", "1" if self.ack_num == 1 else "0", 2)
            acknowledgement.set_header_field("ack", "1", 2)
            self.socket.sendto(acknowledgement.to_byte(), self.client_addr)

            return Server.STATE.RECEIVE
        except:
            return Server.STATE.ERROR

    def receive(self):
        try:
            raw, addr = self.socket.recvfrom(65535)
            if addr != self.client_addr:
                return Server.STATE.RECEIVE
            else:
                packet = Packet(raw)
                seq = packet.get_header_field("seq_num", 10)
                ack = packet.get_header_field("ack_num", 10)
                payload = packet.get_payload()
                if seq == str(self.ack_num):
                    print(payload, end="")
                    return Server.STATE.ACKNOWLEDGE
                else:
                    return Server.STATE.RECEIVE
        except:
            return Server.STATE.ERROR


if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.bind(INADDR_ANY, 5000)
    while True:
        reliableUDP.accept()

        while data := reliableUDP.receive():
            print(data, end="")

        print("")


    

    # server = Server(port = 3000)
    # fms = FSM(
    #     transitions=[
    #         { "source": FSM.STATE.START, "dest": Server.STATE.HANDLE_ARGS, "action": server.handle_args },
    #         { "source": Server.STATE.HANDLE_ARGS, "dest": FSM.STATE.EXIT, "action": server.print_invalid_args },
    #         { "source": Server.STATE.HANDLE_ARGS, "dest": Server.STATE.CREATE_SOCKET, "action": server.create_socket },
    #         { "source": Server.STATE.CREATE_SOCKET, "dest": Server.STATE.ERROR, "action": server.print_error },
    #         { "source": Server.STATE.CREATE_SOCKET, "dest": Server.STATE.BIND_SOCKET, "action": server.bind_socket },
    #         { "source": Server.STATE.BIND_SOCKET, "dest": Server.STATE.ERROR, "action": server.print_error },
    #         { "source": Server.STATE.BIND_SOCKET, "dest": Server.STATE.RECEIVE, "action": server.receive_data },
    #         { "source": Server.STATE.RECEIVE, "dest": Server.STATE.ERROR, "action": server.print_error },
    #         { "source": Server.STATE.RECEIVE, "dest": Server.STATE.PROCESS_DATA, "action": server.process_data },
    #         { "source": Server.STATE.PROCESS_DATA, "dest": Server.STATE.ERROR, "action": server.print_error },
    #         { "source": Server.STATE.PROCESS_DATA, "dest": Server.STATE.ACKNOWLEDGE, "action": server.acknowledge },
    #         { "source": Server.STATE.ACKNOWLEDGE, "dest": Server.STATE.ERROR, "action": server.print_error },
    #         { "source": Server.STATE.ACKNOWLEDGE, "dest": Server.STATE.RECEIVE, "action": server.receive_data },
    #         { "source": Server.STATE.ERROR, "dest": Server.STATE.CLEAN_UP, "action": server.clean_up },
    #         { "source": Server.STATE.CLEAN_UP, "dest": FSM.STATE.EXIT, "action": None },
    #     ], 
    #     initial_state=Server.STATE.HANDLE_ARGS,
    #     verbose=True
    # )
    # fms.run()
    
