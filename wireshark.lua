-- Define custom protocol
my_proto = Proto("reliableUDP", "Custom Reliable UDP")

-- Define fields
local f_seq_num = ProtoField.uint16("reliableUDP.seq_num", "Sequence Number", base.DEC)
local f_ack_num = ProtoField.uint16("reliableUDP.ack_num", "Acknowledgment Number", base.DEC)
local f_flags = ProtoField.uint8("reliableUDP.flags", "Flags", base.HEX)
local f_syn = ProtoField.bool("reliableUDP.flags.syn", "SYN", 8, nil, 0x80)
local f_ack = ProtoField.bool("reliableUDP.flags.ack", "ACK", 8, nil, 0x40)
local f_fin = ProtoField.bool("reliableUDP.flags.fin", "FIN", 8, nil, 0x20)
local f_rst = ProtoField.bool("reliableUDP.flags.rst", "RST", 8, nil, 0x10)
local f_offset = ProtoField.uint8("reliableUDP.flags.offset", "Offset", base.DEC, nil, 0x0F)

-- Add fields to protocol
my_proto.fields = {f_seq_num, f_ack_num, f_flags, f_syn, f_ack, f_fin, f_rst, f_offset}

-- Dissector function
function my_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "ReliableUDP"

    local subtree = tree:add(my_proto, buffer(), "Custom Reliable UDP Protocol Data")

    subtree:add(f_seq_num, buffer(0, 2))
    subtree:add(f_ack_num, buffer(2, 2))

    -- Flags
    local flags = buffer(4, 1)
    local flags_subtree = subtree:add(f_flags, flags)
    flags_subtree:add(f_syn, flags)
    flags_subtree:add(f_ack, flags)
    flags_subtree:add(f_fin, flags)
    flags_subtree:add(f_rst, flags)
    flags_subtree:add(f_offset, flags)
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(1000, my_proto)
udp_port:add(2000, my_proto)
udp_port:add(3000, my_proto)
udp_port:add(4000, my_proto)
udp_port:add(5000, my_proto)
udp_port:add(6000, my_proto)
udp_port:add(7000, my_proto)
udp_port:add(8000, my_proto)
udp_port:add(9000, my_proto)
