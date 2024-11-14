from utils.reliableUDP import ReliableUDP
from socket import  INADDR_ANY 

if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.bind(INADDR_ANY, 5000)
    while True:
        reliableUDP.accept()
        print("connected")

        message, = reliableUDP.receive()
        print(message)

