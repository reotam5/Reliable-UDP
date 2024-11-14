from utils.reliableUDP import ReliableUDP

if __name__ == "__main__":
    reliableUDP = ReliableUDP().create()
    reliableUDP.connect("127.0.0.1", 4000)
    print("connected")

    reliableUDP.send_all("abcdefg")
    reliableUDP.close()
