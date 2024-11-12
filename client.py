from utils.reliableUDP import ReliableUDP

if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.connect("127.0.0.1", 4000)
    
    reliableUDP.send_all("hello\n")
    reliableUDP.send_all("next")
    reliableUDP.close()
