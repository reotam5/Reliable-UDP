from utils.reliableUDP import ReliableUDP

if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.send("abc", "127.0.0.1", 4000)
