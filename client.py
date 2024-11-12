from enum import Enum
from utils.reliableUDP import ReliableUDP
from utils.fsm import FSM
from socket import AF_INET, SOCK_DGRAM, socket 
import ipaddress

from utils.packet import Packet

class Client():
    class STATE(Enum):
        HANDLE_ARGS = "HANDLE_ARGS"
        CREATE_SOCKET = "CREATE_SOCKET"
        SEND_DATA = "SEND_DATA"
        WAIT_ACK = "WAIT_ACK"
        TIMEOUT = "TIMEOUT"
        DUPLICATE_ACK = "DUPLICATE_ACK"
        SUCCESS = "SUCCESS"
        RETRANSMIT = "RETRANSMIT"
        ERROR = "ERROR"
        CLEAN_UP = "CLEAN_UP"

    def __init__(self, ip, port, data):
        self.port = port
        self.ip = ip
        self.socket: socket
        self.data = data.encode()
        self.seqNum = 0
        self.acknowledged = 0
        self.error = None


    def create_socket(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.settimeout(2)
        if socket:
            return Client.STATE.SEND_DATA
        else:
            return Client.STATE.ERROR

    def send_data(self):
        try:
            packet = Packet() 
            packet.set_header_field("seq_num", "1", 10)
            packet.set_header_field("ack_num", "2", 10)
            packet.set_header_field("syn", "1", 2)
            packet.set_header_field("ack", "0", 2)
            packet.set_header_field("fin", "1", 2)
            packet.set_header_field("payload_length", "16", 10)
            packet.set_payload("wow this worked.")

            self.socket.sendto(packet.to_byte(), (str(ipaddress.ip_address(self.ip)), self.port))
            self.seqNum += 1
            if self.seqNum - self.acknowledged > 1 or len(self.data) == self.seqNum:
                return Client.STATE.WAIT_ACK
            else:
                return Client.STATE.SEND_DATA
        except Exception as e:
            self.error = e
            return Client.STATE.ERROR

    def receive_ack(self):
        try:
            ack, _ = self.socket.recvfrom(1024)
            print(_)
            print(ack.decode())
            ack_num = int(ack.decode())
            print('received ack')
            print(ack_num)

            if ack_num > self.acknowledged:
                self.acknowledged += 10
                return Client.STATE.SUCCESS
            elif ack_num <= self.acknowledged:
                return Client.STATE.DUPLICATE_ACK
            return Client.STATE.TIMEOUT
        except Exception as e:
            self.error = e
            return Client.STATE.ERROR

    def retransmit(self):
        self.seqNum = self.acknowledged
        return Client.STATE.SEND_DATA


    def print_error(self):
        print(self.error)
        return Client.STATE.CLEAN_UP

    def clean_up(self):
        if self.socket:
            self.socket.close()
        return FSM.STATE.EXIT


if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.connect("127.0.0.1", 4000)
    
    reliableUDP.send_all("hello\n")
    reliableUDP.send_all("next")
    reliableUDP.close()
    # response = reliableUDP.receive()
    # print("response: {val}".format(val=response))
    # reliableUDP.close()
    



    # client = Client(ip="127.0.0.1",port = 3000, data="hello")
    # fms = FSM(
    #     transitions=[
    #         { "source": FSM.STATE.START, "dest": Client.STATE.HANDLE_ARGS, "action": client.handle_args },
    #         { "source": Client.STATE.HANDLE_ARGS, "dest": FSM.STATE.EXIT, "action": client.print_invalid_args },
    #         { "source": Client.STATE.HANDLE_ARGS, "dest": Client.STATE.CREATE_SOCKET, "action": client.create_socket },
    #         { "source": Client.STATE.CREATE_SOCKET, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.CREATE_SOCKET, "dest": Client.STATE.SEND_DATA, "action": client.send_data },
    #         { "source": Client.STATE.SEND_DATA, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.SEND_DATA, "dest": Client.STATE.SEND_DATA, "action": client.send_data },
    #         { "source": Client.STATE.SEND_DATA, "dest": Client.STATE.WAIT_ACK, "action": client.receive_ack },
    #         { "source": Client.STATE.WAIT_ACK, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.WAIT_ACK, "dest": Client.STATE.SUCCESS, "action": client.send_data },
    #         { "source": Client.STATE.WAIT_ACK, "dest": Client.STATE.TIMEOUT, "action": lambda: Client.STATE.RETRANSMIT },
    #         { "source": Client.STATE.WAIT_ACK, "dest": Client.STATE.DUPLICATE_ACK, "action": lambda: Client.STATE.RETRANSMIT },
    #         { "source": Client.STATE.SUCCESS, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.SUCCESS, "dest": Client.STATE.SEND_DATA, "action": client.send_data },
    #         { "source": Client.STATE.TIMEOUT, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.TIMEOUT, "dest": Client.STATE.RETRANSMIT, "action": client.retransmit },
    #         { "source": Client.STATE.DUPLICATE_ACK, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.DUPLICATE_ACK, "dest": Client.STATE.RETRANSMIT, "action": client.retransmit },
    #         { "source": Client.STATE.RETRANSMIT, "dest": Client.STATE.ERROR, "action": client.print_error },
    #         { "source": Client.STATE.RETRANSMIT, "dest": Client.STATE.SEND_DATA, "action": client.send_data },
    #         { "source": Client.STATE.ERROR, "dest": Client.STATE.CLEAN_UP, "action": client.clean_up },
    #         { "source": Client.STATE.CLEAN_UP, "dest": FSM.STATE.EXIT, "action": None },
    #     ], 
    #     initial_state=Client.STATE.HANDLE_ARGS,
    #     verbose=True
    # )
    # fms.run()
    
