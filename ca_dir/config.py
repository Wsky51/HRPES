import struct


ca_port = 2900
BUF_SIZE=1024


def stg_send(socket,data):
    size=len(data)
    # 先告知对端目前要发送的数据量大小是多少
    socket.send(struct.pack('L', size))
    socket.send(data)

def stg_recv(socket):
    data_info_size = struct.calcsize('L')
    # 接收大小信息
    buf = socket.recv(data_info_size)
    # 接收端接受数据大小信息
    data_size = struct.unpack('L', buf)[0]
    recvd_size = 0  # 定义已接收文件的大小

    gap_abs = data_size % BUF_SIZE
    count = data_size // BUF_SIZE
    recv_data = b''
    for i in range(count):
        data = socket.recv(BUF_SIZE)
        recv_data += data
    recv_data += socket.recv(gap_abs)
    return recv_data

def str_encode_utf8(strdata):
    return bytes(strdata, encoding='utf-8')

def utf8_decode_str(data):
    return str(data, encoding='utf-8')