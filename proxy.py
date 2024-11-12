import ipaddress
import sys
from socket import AF_INET, socket, SOCK_DGRAM
import random
import time
from typing import Any 
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QLabel
from PyQt6.QtCore import Qt


class Proxy(QMainWindow):
    def __init__(self, listen_ip, listen_port: int, target_ip: str, target_port: int, client_drop: int, client_delay: int, client_delay_time: float, server_drop: float, server_delay: float, server_delay_time: float):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.client_delay = client_delay
        self.client_delay_time = client_delay_time
        self.server_drop = server_drop
        self.server_delay = server_delay
        self.server_delay_time = server_delay_time
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.client_addr: Any

        super().__init__()
        self.setWindowTitle("Proxy parameters")
        self.setFixedSize(300, 150)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMinimum(100)
        self.slider.setValue(client_drop)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.client_drop_label = QLabel("Value: {val}".format(val=self.slider.value()))
        self.client_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.client_drop_label.setStyleSheet("QLabel { font-size: 16px; }")

        layout.addSpacing(20)
        layout.addWidget(self.slider)
        layout.addWidget(self.client_drop_label)
        layout.addSpacing(20)

        self.slider.valueChanged.connect(lambda value: self.client_drop_label.setText("Value: {val}".format(val=value)))



    def run(self):
        self.socket.bind((str(ipaddress.ip_address(self.listen_ip)), self.listen_port))
        while True:
            data, (ip, port) = self.socket.recvfrom(65535)
            is_server = ip == self.target_ip and port == self.target_port
            if not is_server:
                self.client_addr = (ip, port)
            forward_to = (str(ipaddress.ip_address(self.client_addr[0] if is_server else self.target_ip)), self.client_addr[1] if is_server else self.target_port)
            print('==============')
            print('received from ', (ip, port))
            print('forwarding to ', forward_to)
            print('==============')
            drop_prob = self.server_drop if is_server else self.slider.value()
            delay_prob = self.server_delay if is_server else self.client_delay
            delay_time = self.server_delay_time if is_server else self.client_delay_time
            
            shouldDrop = random.random() <= (drop_prob / 100)
            shouldDelay = random.random() <= (delay_prob / 100)
            if shouldDrop:
                continue
            if shouldDelay:
                time.sleep(delay_time / 1000)
            self.socket.sendto(data, forward_to)
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    proxy = Proxy(
        listen_ip="0.0.0.0",
        listen_port=4000,
        target_ip="127.0.0.1",
        target_port=5000,
        client_drop=80,
        client_delay=80,
        client_delay_time=1000,
        server_drop=80,
        server_delay=80,
        server_delay_time=1000,
    )
    proxy.show()
    proxy.run()
    sys.exit(app.exec())



