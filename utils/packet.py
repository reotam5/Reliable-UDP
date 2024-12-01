from typing import Optional, Union 

custom_header = {
    "seq_num": 2,
    "ack_num": 2,
    "syn": 1/8,
    "ack": 1/8,
    "fin": 1/8,
    "offset": 5/8, # offset to make header length nice number
}

class Packet():
    def __init__(self, packet: Optional[bytes] = None, header_definition = custom_header):
        self.header_definition = header_definition
        self.header_length_bits = int(sum(header_definition.values()) * 8)
        self.binary = bin(int(packet.hex(), 16))[2:].zfill(len(packet.hex()) * 4) if packet else "0" * self.header_length_bits


    def get_header_field_position(self, field_name):
        bit_pointer = 0
        for key, size in self.header_definition.items():
            if key == field_name:
                bit_length = int(size * 8)
                return (bit_pointer, bit_pointer + bit_length)
            bit_pointer += int(size * 8)
        raise ValueError(f"Field '{field_name}' not found in header definition")


    def get_header_field(self, field_name: str, base: int = 16):
        bit_start, bit_end = self.get_header_field_position(field_name)
        binary_value = self.binary[bit_start:bit_end]

        if base == 2:
            return binary_value
        elif base == 10:
            return str(int(binary_value, 2))
        elif base == 16:
            return hex(int(binary_value, 2))[2:]
        else:
            raise ValueError("Unsupported base")


    def set_header_field(self, field_name: str, value: str, base = 16):
        bit_start, bit_end = self.get_header_field_position(field_name)

        if base == 16:
            binary_value = bin(int(value, 16))[2:]
        elif base == 10:
            binary_value = bin(int(value))[2:]
        elif base == 2:
            binary_value = value
        else:
            raise ValueError("Unsupported base")

        field_length = bit_end - bit_start
        binary_value = binary_value.zfill(field_length)[-field_length:]
        self.binary = self.binary[:bit_start] + binary_value + self.binary[bit_end:]


    def set_payload(self, data: str):
        if len(data) == 0:
            return
        payload_hex = data.encode().hex()
        payload_binary = bin(int(payload_hex, 16))[2:].zfill(len(payload_hex) * 4)
        self.binary = self.binary[:self.header_length_bits] + payload_binary


    def get_payload(self) -> Union[str, None]:
        payload_binary = self.binary[self.header_length_bits:]
        if len(payload_binary) == 0:
            return None
        payload_hex = hex(int(payload_binary, 2))[2:].zfill(len(payload_binary) // 4)
        return bytes.fromhex(payload_hex).decode()


    def get_hex(self) -> str:
        return hex(int(self.binary, 2))[2:].zfill(len(self.binary) // 4)


    def to_byte(self) -> bytes:
        return bytes.fromhex(self.get_hex())

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Packet):
            return value.get_hex() == self.get_hex()
        return False


