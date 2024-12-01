import ipaddress
import random
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from socket import AF_INET, SOCK_DGRAM, socket
from utils.cli import CLI
from utils.packet import Packet
from utils.proxy.argparser import ArgParser
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys

class Proxy:
    MAX_MEMORY = 500

    def __init__(
        self,
        listen_ip,
        listen_port: int,
        target_ip: str,
        target_port: int,
        client_drop: int,
        client_delay: int,
        client_delay_time: tuple[float, float],
        server_drop: float,
        server_delay: float,
        server_delay_time: tuple[float, float],
    ):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.client_config = {
            "ip": None,
            "port": None,
            "drop": client_drop,
            "delay": client_delay,
            "delay_time": client_delay_time,
        }
        self.server_config = {
            "ip": target_ip,
            "port": target_port,
            "drop": server_drop,
            "delay": server_delay,
            "delay_time": server_delay_time,
        }
        self.packets = []
        self.live_stats = {
            "client_sent": 0,
            "client_received": 0,
            "client_dropped": 0,
            "client_retransmitted": 0,
            "client_latency": [],
            "server_sent": 0,
            "server_received": 0,
            "server_dropped": 0,
            "server_retransmitted": 0,
            "server_latency": [],
        }

    def set_config(self, target, field, value):
        config = self.client_config if target == "client" else self.server_config
        config[field] = value

    def get_config(self, target, field):
        config = self.client_config if target == "client" else self.server_config
        return config[field]

    def forward(self, data, forawrd_to, delay, drop, is_source_server):
        if delay:
            time.sleep(delay/1000)
        self.record_packet(is_source_server, data, drop, delay)
        if drop:
            return
        self.socket.sendto(data, forawrd_to)

    def record_packet(self, is_source_server, data, is_dropped, delay_time):
        source = "server" if is_source_server else "client"
        packet = Packet(data)
        self.live_stats[f"{source}_sent"] += 1

        if is_dropped:
            self.live_stats[f"{source}_dropped"] += 1
        else:
            self.live_stats[f"{"client" if is_source_server else "server"}_received"] += 1
            self.live_stats[f"{source}_latency"].append(delay_time or 0)

        if packet in self.packets:
            self.live_stats[f"{source}_retransmitted"] += 1
        self.packets.append(packet)
        if len(self.packets) > Proxy.MAX_MEMORY:
            self.packets.pop(0)

    def live_graph(self):
        fig, ((client_ax1, server_ax1), (client_ax2, server_ax2)) = plt.subplots(2, 2, figsize=(15, 8))
        def update(_):
            table = {
                "client": (client_ax1, client_ax2),
                "server": (server_ax1, server_ax2),
            }
            for target in table:
                ax1, ax2 = table[target]
                ax1.clear()
                ax2.clear()

                labels = ["sent", "received", "dropped", "retransmitted"]
                metrics = [target + "_" + x for x in labels]
                values = [self.live_stats[m] for m in metrics]
                ax1.bar(labels, values, color=["blue", "green", "red", "purple"])
                ax1.set_title(f"Packet Stats - {target}")
                ax1.set_ylabel("Count")

                latencies = self.live_stats[f"{target}_latency"]
                ax2.plot(latencies[-50:], label="Latency (last 50 packets)", color="black")
                ax2.set_title(f"Latency Observed - {target}")
                ax2.set_ylabel("Milliseconds")
                ax2.set_xlabel("Packet Index")
                ax2.legend()
            return fig,

        _ = FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
        plt.show()

    def recv_packet(self):
        with ThreadPoolExecutor() as executor:
            while True:
                data, (ip, port) = self.socket.recvfrom(1024)
                is_server = (
                    ip == self.server_config["ip"] and port == self.server_config["port"]
                )
                if not is_server:
                    self.client_config["ip"] = ip
                    self.client_config["port"] = port
                forward_to = (
                    str(
                        ipaddress.ip_address(
                            self.client_config["ip"]
                            if is_server
                            else self.server_config["ip"]
                        )
                    ),
                    self.client_config["port"] if is_server else self.server_config["port"],
                )
                config = self.server_config if is_server else self.client_config
                drop_prob = config["drop"]
                delay_prob = config["delay"]
                delay_time_min, delay_time_max = config["delay_time"]
                delay_time = random.uniform(delay_time_min, delay_time_max or delay_time_min)

                should_drop = random.random() <= (drop_prob / 100)
                should_delay = random.random() <= (delay_prob / 100)
                executor.submit(self.forward, data, forward_to, delay_time if (should_delay and not should_drop) else None, should_drop, is_server)

    def run(self):
        self.socket.bind((str(ipaddress.ip_address(self.listen_ip)), self.listen_port))
        self.recv_packet()

    def stop(self):
        self.socket.close()


def signal_handler(_sig, _frame, proxy: Proxy, cli: CLI):
    print("Shutting down gracefully...")
    proxy.stop()  # Stop the proxy loop
    cli.stop()
    sys.exit(0)


if __name__ == "__main__":
    parser = ArgParser()

    proxy = Proxy(
        listen_ip=parser.listen_ip,
        listen_port=parser.listen_port,
        target_ip=parser.target_ip,
        target_port=parser.target_port,
        client_drop=parser.client_drop,
        client_delay=parser.client_delay,
        client_delay_time=parser.client_delay_time,
        server_drop=parser.server_drop,
        server_delay=parser.server_delay,
        server_delay_time=parser.server_delay_time,
    )
    cli = CLI(
        [
            str(parser),
            "Proxy Parameters",
            "UP/DOWN arrows to select value, LEFT/RIGHT to adjust",
        ],
        [
            {
                "name": "Client drop",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("client", "drop"),
                "set_value": lambda x: proxy.set_config("client", "drop", x),
            },
            {
                "name": "Client delay",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("client", "delay"),
                "set_value": lambda x: proxy.set_config("client", "delay", x),
            },
            {
                "name": "Client delay time - min",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("client", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("client", "delay_time", (min(x, proxy.get_config("client", "delay_time")[1]),proxy.get_config("client", "delay_time")[1])),
            },
            {
                "name": "Client delay time - max",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("client", "delay_time")[1],
                "set_value": lambda x: proxy.set_config("client", "delay_time", (proxy.get_config("client", "delay_time")[0], max(x, proxy.get_config("client", "delay_time")[0]))),
            },
            {
                "name": "Server drop",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("server", "drop"),
                "set_value": lambda x: proxy.set_config("server", "drop", x),
            },
            {
                "name": "Server delay",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "%",
                "get_value": lambda: proxy.get_config("server", "delay"),
                "set_value": lambda x: proxy.set_config("server", "delay", x),
            },
            {
                "name": "Server delay time - min",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("server", "delay_time")[0],
                "set_value": lambda x: proxy.set_config("server", "delay_time", (min(x, proxy.get_config("server", "delay_time")[1]),proxy.get_config("server", "delay_time")[1])),
            },
            {
                "name": "Server delay time - max",
                "min": 0,
                "step": 100,
                "suffix": "ms",
                "get_value": lambda: proxy.get_config("server", "delay_time")[1],
                "set_value": lambda x: proxy.set_config("server", "delay_time", (proxy.get_config("server", "delay_time")[0],max(x, proxy.get_config("server", "delay_time")[0]))),
            },
        ],
        10,
    )

    # Register signal handler
    signal.signal(
        signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, proxy, cli)
    )


    proxy_thread = Thread(target=proxy.run, daemon=True)
    cli_thread = Thread(target=cli.start, daemon=True)

    proxy_thread.start()
    cli_thread.start()

    proxy.live_graph()
    proxy_thread.join()
    cli_thread.join()

    sys.exit(0)
