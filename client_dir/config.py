import struct

server_ip = "127.0.0.1"
server_port = 2196
BUF_SIZE= 1024
URL="http://www.chinadaily.com.cn/"
ca_pub_key = [9491, 117605212259] #保留CA中心的公钥，用来模拟CA数字中心的签发
aes_key = "abcdefghijklmnop" #设定AES对称加密算法的密钥

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
